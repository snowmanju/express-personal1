"""
属性测试：重复处理
Property Test: Duplicate Handling

**Feature: csv-file-upload, Property 16: Duplicate Handling**
**Validates: Requirements 7.3**

测试清单存储器在遇到重复快递单号时正确更新现有记录
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


@settings(max_examples=100, deadline=None)
@given(
    initial_records=st.lists(valid_manifest_record(), min_size=1, max_size=10, unique_by=lambda r: r.tracking_number),
    data=st.data()
)
def test_property_duplicate_tracking_numbers_update_existing_records(initial_records, data):
    """
    属性16：重复处理
    
    对于任何已存在于数据库中的快递单号，CSV_Processor应该更新现有记录而不是插入新记录
    
    验证：需求7.3
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 首次保存记录
        result1 = storage.save_manifest_records(initial_records)
        assert result1.success, f"首次保存失败: {result1.errors}"
        assert result1.inserted == len(initial_records), \
            f"插入数量不匹配: 期望 {len(initial_records)}, 实际 {result1.inserted}"
        assert result1.updated == 0, "首次保存不应该有更新"
        
        # 获取初始数据
        initial_data = {}
        for record in initial_records:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == record.tracking_number
            ).first()
            initial_data[record.tracking_number] = {
                'id': db_record.id,
                'manifest_date': db_record.manifest_date,
                'transport_code': db_record.transport_code,
                'customer_code': db_record.customer_code,
                'goods_code': db_record.goods_code
            }
        
        # 创建更新记录（使用相同的快递单号但不同的数据）
        updated_records = []
        for record in initial_records:
            updated_record = ManifestRecord(
                tracking_number=record.tracking_number,  # 相同的快递单号
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
        assert result2.inserted == 0, "不应该插入新记录"
        assert result2.updated == len(updated_records), \
            f"更新数量不匹配: 期望 {len(updated_records)}, 实际 {result2.updated}"
        
        # 验证记录总数没有增加
        total_records = test_db.query(CargoManifest).count()
        assert total_records == len(initial_records), \
            f"记录总数应该保持不变: 期望 {len(initial_records)}, 实际 {total_records}"
        
        # 验证记录已更新
        for updated_record in updated_records:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == updated_record.tracking_number
            ).first()
            
            # 验证ID没有改变（说明是更新而不是删除后插入）
            assert db_record.id == initial_data[updated_record.tracking_number]['id'], \
                f"记录ID不应该改变: {updated_record.tracking_number}"
            
            # 验证数据已更新
            assert str(db_record.manifest_date) == updated_record.manifest_date, \
                f"manifest_date应该更新: {updated_record.tracking_number}"
            assert db_record.transport_code == updated_record.transport_code, \
                f"transport_code应该更新: {updated_record.tracking_number}"
            assert db_record.customer_code == updated_record.customer_code, \
                f"customer_code应该更新: {updated_record.tracking_number}"
            assert db_record.goods_code == updated_record.goods_code, \
                f"goods_code应该更新: {updated_record.tracking_number}"


@settings(max_examples=50, deadline=None)
@given(
    existing_records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number),
    new_records=st.lists(valid_manifest_record(), min_size=1, max_size=5, unique_by=lambda r: r.tracking_number)
)
def test_property_mixed_new_and_duplicate_records(existing_records, new_records):
    """
    属性16扩展：混合新记录和重复记录
    
    当批量保存包含新记录和重复记录的混合数据时，应该正确插入新记录并更新重复记录
    
    验证：需求7.3
    """
    with get_test_db() as test_db:
        storage = ManifestStorage(test_db)
        
        # 首先保存现有记录
        result1 = storage.save_manifest_records(existing_records)
        assert result1.success, f"首次保存失败: {result1.errors}"
        
        # 创建混合记录列表：一半是重复的，一半是新的
        # 确保新记录的快递单号与现有记录不重复
        existing_tracking_numbers = {r.tracking_number for r in existing_records}
        filtered_new_records = [r for r in new_records if r.tracking_number not in existing_tracking_numbers]
        
        if not filtered_new_records:
            # 如果没有新记录，跳过此测试
            return
        
        # 选择一半现有记录进行更新
        num_to_update = max(1, len(existing_records) // 2)
        records_to_update = existing_records[:num_to_update]
        
        # 创建更新版本的记录
        updated_versions = []
        for record in records_to_update:
            updated_versions.append(ManifestRecord(
                tracking_number=record.tracking_number,
                manifest_date=record.manifest_date,
                transport_code=record.transport_code + "_updated",
                customer_code=record.customer_code,
                goods_code=record.goods_code,
                package_number=record.package_number,
                length=record.length,
                width=record.width,
                height=record.height,
                weight=record.weight
            ))
        
        # 混合记录：更新的 + 新的
        mixed_records = updated_versions + filtered_new_records[:5]
        
        # 保存混合记录
        result2 = storage.save_manifest_records(mixed_records)
        assert result2.success, f"混合保存失败: {result2.errors}"
        
        # 验证插入和更新数量
        assert result2.inserted == len(filtered_new_records[:5]), \
            f"插入数量不匹配: 期望 {len(filtered_new_records[:5])}, 实际 {result2.inserted}"
        assert result2.updated == len(updated_versions), \
            f"更新数量不匹配: 期望 {len(updated_versions)}, 实际 {result2.updated}"
        
        # 验证总记录数
        expected_total = len(existing_records) + len(filtered_new_records[:5])
        actual_total = test_db.query(CargoManifest).count()
        assert actual_total == expected_total, \
            f"总记录数不匹配: 期望 {expected_total}, 实际 {actual_total}"
        
        # 验证更新的记录确实被更新了
        for updated_record in updated_versions:
            db_record = test_db.query(CargoManifest).filter(
                CargoManifest.tracking_number == updated_record.tracking_number
            ).first()
            assert db_record.transport_code == updated_record.transport_code, \
                f"记录应该被更新: {updated_record.tracking_number}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
