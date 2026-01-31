"""
属性测试：带时间戳的数据持久化
Property Test: Data Persistence with Timestamps

**Feature: csv-file-upload, Property 15: Data Persistence with Timestamps**
**Validates: Requirements 7.1, 7.2**

测试清单存储器在保存模式下正确存储有效的清单记录，并包含适当的时间戳
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base
from app.services.manifest_storage import ManifestStorage, ManifestRecord, StorageResult
from app.models.cargo_manifest import CargoManifest


@contextmanager
def get_test_db():
    """创建测试数据库会话的上下文管理器"""
    # 为每次调用创建新的内存数据库
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


@settings(max_examples=100, deadline=None)
@given(records=st.lists(valid_manifest_record(), min_size=1, max_size=10, unique_by=lambda r: r.tracking_number))
def test_property_data_persistence_with_timestamps(records):
    """
    属性15：带时间戳的数据持久化
    
    对于任何有效的清单记录在保存模式下，CSV_Processor应该将它们存储到数据库，
    并包含适当的created_at和updated_at时间戳
    
    验证：需求7.1、7.2
    """
    with get_test_db() as test_db:
        # 记录测试开始时间
        test_start_time = datetime.now()
        
        # 创建存储器实例
        storage = ManifestStorage(test_db)
        
        # 保存记录
        result = storage.save_manifest_records(records)
        
        # 验证保存成功
        assert result.success, f"保存失败: {result.errors}"
        assert result.inserted == len(records), f"插入数量不匹配: 期望 {len(records)}, 实际 {result.inserted}"
        
        # 验证所有记录都已存储到数据库
        for record in records:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == record.tracking_number
            ).first()
            
            # 验证记录存在
            assert db_record is not None, f"记录未找到: {record.tracking_number}"
            
            # 验证数据正确性
            assert db_record.tracking_number == record.tracking_number
            if record.manifest_date:
                assert str(db_record.manifest_date) == record.manifest_date
            if record.transport_code:
                assert db_record.transport_code == record.transport_code
            if record.customer_code:
                assert db_record.customer_code == record.customer_code
            if record.goods_code:
                assert db_record.goods_code == record.goods_code
            
            # 验证时间戳存在
            assert db_record.created_at is not None, "created_at时间戳缺失"
            assert db_record.updated_at is not None, "updated_at时间戳缺失"
            
            # 验证时间戳在合理范围内（测试开始后，当前时间前）
            test_end_time = datetime.now()
            assert test_start_time <= db_record.created_at <= test_end_time, \
                f"created_at时间戳不在合理范围内: {db_record.created_at}"
            assert test_start_time <= db_record.updated_at <= test_end_time, \
                f"updated_at时间戳不在合理范围内: {db_record.updated_at}"
            
            # 对于新插入的记录，created_at和updated_at应该相同或非常接近
            time_diff = abs((db_record.updated_at - db_record.created_at).total_seconds())
            assert time_diff < 1.0, \
                f"新记录的created_at和updated_at时间差过大: {time_diff}秒"


@settings(max_examples=50, deadline=None)
@given(
    initial_records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number),
    data=st.data()
)
def test_property_updated_at_timestamp_changes(initial_records, data):
    """
    属性15扩展：验证updated_at时间戳在更新时改变
    
    当更新现有记录时，updated_at时间戳应该更新，而created_at保持不变
    
    验证：需求7.2
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 首次保存记录
        result1 = storage.save_manifest_records(initial_records)
        assert result1.success, f"首次保存失败: {result1.errors}"
        
        # 获取初始时间戳
        initial_timestamps = {}
        for record in initial_records:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == record.tracking_number
            ).first()
            initial_timestamps[record.tracking_number] = {
                'created_at': db_record.created_at,
                'updated_at': db_record.updated_at
            }
        
        # 等待一小段时间以确保时间戳会不同
        import time
        time.sleep(0.1)
        
        # 创建更新记录（使用相同的快递单号但不同的数据）
        updated_records = []
        for record in initial_records:
            updated_record = ManifestRecord(
                tracking_number=record.tracking_number,
                manifest_date=data.draw(valid_date_string),
                transport_code=data.draw(valid_code),
                customer_code=data.draw(valid_code),
                goods_code=data.draw(valid_code),
                package_number=data.draw(st.one_of(st.none(), valid_code)),
                length=data.draw(st.one_of(st.none(), valid_dimension)),
                width=data.draw(st.one_of(st.none(), valid_dimension)),
                height=data.draw(st.one_of(st.none(), valid_dimension)),
                weight=data.draw(st.one_of(st.none(), valid_dimension))
            )
            updated_records.append(updated_record)
        
        # 再次保存（应该更新现有记录）
        result2 = storage.save_manifest_records(updated_records)
        assert result2.success, f"更新保存失败: {result2.errors}"
        assert result2.updated == len(updated_records), \
            f"更新数量不匹配: 期望 {len(updated_records)}, 实际 {result2.updated}"
        
        # 验证时间戳变化
        for record in updated_records:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == record.tracking_number
            ).first()
            
            initial_ts = initial_timestamps[record.tracking_number]
            
            # created_at应该保持不变
            assert db_record.created_at == initial_ts['created_at'], \
                f"created_at不应该改变: 初始 {initial_ts['created_at']}, 当前 {db_record.created_at}"
            
            # updated_at应该更新
            assert db_record.updated_at >= initial_ts['updated_at'], \
                f"updated_at应该更新: 初始 {initial_ts['updated_at']}, 当前 {db_record.updated_at}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
