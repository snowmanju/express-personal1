"""
属性测试：存储错误恢复
Property Test: Storage Error Recovery

**Feature: csv-file-upload, Property 17: Storage Error Resilience**
**Validates: Requirements 7.4**

测试清单存储器在遇到存储错误时的恢复能力，确保部分失败不影响其他记录的处理
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.database import Base
from app.services.manifest_storage import ManifestStorage, ManifestRecord
from app.models.cargo_manifest import CargoManifest


@contextmanager
def get_test_db():
    """创建测试数据库会话的上下文管理器"""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


# 策略：生成有效的快递单号
valid_tracking_number = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=5,
    max_size=50
).filter(lambda x: x.strip() != '')


# 策略：生成有效的日期字符串
valid_date_string = st.dates(
    min_value=datetime(2020, 1, 1).date(),
    max_value=datetime(2030, 12, 31).date()
).map(lambda d: d.strftime('%Y-%m-%d'))


# 策略：生成有效的代码
valid_code = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1,
    max_size=20
).filter(lambda x: x.strip() != '')


# 策略：生成有效的尺寸值
valid_dimension = st.floats(min_value=0.01, max_value=9999.99, allow_nan=False, allow_infinity=False)


# 策略：生成有效的ManifestRecord
@st.composite
def valid_manifest_record(draw):
    """生成有效的清单记录"""
    return ManifestRecord(
        tracking_number=draw(valid_tracking_number),
        manifest_date=draw(valid_date_string),
        transport_code=draw(valid_code),
        customer_code=draw(valid_code),
        goods_code=draw(valid_code),
        package_number=draw(st.one_of(st.none(), valid_code)),
        length=draw(st.one_of(st.none(), valid_dimension)),
        width=draw(st.one_of(st.none(), valid_dimension)),
        height=draw(st.one_of(st.none(), valid_dimension)),
        weight=draw(st.one_of(st.none(), valid_dimension))
    )


@settings(max_examples=50, deadline=None)
@given(records=st.lists(valid_manifest_record(), min_size=1, max_size=10, unique_by=lambda r: r.tracking_number))
def test_property_storage_error_returns_failure_result(records):
    """
    属性17：存储错误恢复
    
    当数据库操作失败时，存储器应该返回失败结果并包含错误信息，而不是抛出异常
    
    验证：需求7.4
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 模拟数据库提交失败
        with patch.object(test_db, 'commit', side_effect=SQLAlchemyError("模拟数据库错误")):
            result = storage.save_manifest_records(records)
            
            # 验证返回失败结果而不是抛出异常
            assert result.success is False, "应该返回失败结果"
            assert len(result.errors) > 0, "应该包含错误信息"
            assert "数据库操作失败" in result.errors[0] or "模拟数据库错误" in result.errors[0], \
                f"错误信息应该包含数据库错误: {result.errors}"


@settings(max_examples=30, deadline=None)
@given(records=st.lists(valid_manifest_record(), min_size=2, max_size=10, unique_by=lambda r: r.tracking_number))
def test_property_storage_error_triggers_rollback(records):
    """
    属性17扩展：存储错误触发回滚
    
    当存储操作失败时，应该回滚事务，确保数据库状态一致
    
    验证：需求7.4
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 记录初始记录数
        initial_count = test_db.query(CargoManifest).count()
        
        # 模拟数据库提交失败
        with patch.object(test_db, 'commit', side_effect=SQLAlchemyError("模拟数据库错误")):
            result = storage.save_manifest_records(records)
            assert result.success is False, "应该返回失败结果"
        
        # 验证回滚后数据库状态没有改变
        final_count = test_db.query(CargoManifest).count()
        assert final_count == initial_count, \
            f"回滚后记录数应该保持不变: 初始 {initial_count}, 最终 {final_count}"


@settings(max_examples=30, deadline=None)
@given(
    valid_records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number)
)
def test_property_partial_success_with_transaction_support(valid_records):
    """
    属性17扩展：事务支持确保全有或全无
    
    在事务支持下，要么所有记录都成功保存，要么全部回滚
    
    验证：需求7.4
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 正常保存应该成功
        result1 = storage.save_manifest_records(valid_records)
        assert result1.success is True, f"正常保存应该成功: {result1.errors}"
        
        saved_count = test_db.query(CargoManifest).count()
        assert saved_count == len(valid_records), \
            f"保存的记录数应该匹配: 期望 {len(valid_records)}, 实际 {saved_count}"
        
        # 创建新的记录列表用于测试失败场景
        new_records = []
        for i, record in enumerate(valid_records):
            new_record = ManifestRecord(
                tracking_number=f"NEW_{record.tracking_number}_{i}",
                manifest_date=record.manifest_date,
                transport_code=record.transport_code,
                customer_code=record.customer_code,
                goods_code=record.goods_code,
                package_number=record.package_number,
                length=record.length,
                width=record.width,
                height=record.height,
                weight=record.weight
            )
            new_records.append(new_record)
        
        # 模拟提交失败
        with patch.object(test_db, 'commit', side_effect=SQLAlchemyError("模拟提交失败")):
            result2 = storage.save_manifest_records(new_records)
            assert result2.success is False, "应该返回失败结果"
        
        # 验证失败后记录数没有增加（全部回滚）
        final_count = test_db.query(CargoManifest).count()
        assert final_count == saved_count, \
            f"失败后记录数应该保持不变: 期望 {saved_count}, 实际 {final_count}"


@settings(max_examples=20, deadline=None)
@given(records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number))
def test_property_storage_handles_unexpected_exceptions(records):
    """
    属性17扩展：处理意外异常
    
    存储器应该能够处理各种意外异常，并返回适当的错误结果
    
    验证：需求7.4
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 模拟意外异常
        with patch.object(test_db, 'query', side_effect=Exception("意外错误")):
            result = storage.save_manifest_records(records)
            
            # 验证返回失败结果
            assert result.success is False, "应该返回失败结果"
            assert len(result.errors) > 0, "应该包含错误信息"
            assert "存储操作失败" in result.errors[0] or "意外错误" in result.errors[0], \
                f"错误信息应该包含异常信息: {result.errors}"


@settings(max_examples=20, deadline=None)
@given(records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number))
def test_property_empty_records_list_succeeds(records):
    """
    属性17扩展：空记录列表处理
    
    当传入空记录列表时，存储器应该成功返回而不执行任何操作
    
    验证：需求7.4
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 保存空列表
        result = storage.save_manifest_records([])
        
        # 验证成功返回
        assert result.success is True, "空列表应该成功返回"
        assert result.inserted == 0, "不应该插入任何记录"
        assert result.updated == 0, "不应该更新任何记录"
        assert len(result.errors) == 0, "不应该有错误"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
