"""
属性测试：保存模式持久化
**Feature: csv-file-upload, Property 7: Save Mode Persistence**
**Validates: Requirements 3.2, 3.4**

测试保存模式会将有效数据持久化到数据库
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.services.csv_processor import CSVProcessor
from app.services.data_validator import DataValidator
from app.services.manifest_storage import ManifestStorage
from app.models.cargo_manifest import Base, CargoManifest


# 策略：生成有效的清单数据
@st.composite
def valid_manifest_row(draw):
    """生成有效的清单数据行"""
    return {
        '理货日期': draw(st.sampled_from(['2024-01-15', '2024/01/15', '01/15/2024'])),
        '快递单号': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=5, max_size=20)),
        '集包单号': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=5, max_size=20)),
        '长度': draw(st.floats(min_value=0.1, max_value=1000.0)),
        '宽度': draw(st.floats(min_value=0.1, max_value=1000.0)),
        '高度': draw(st.floats(min_value=0.1, max_value=1000.0)),
        '重量': draw(st.floats(min_value=0.1, max_value=1000.0)),
        '货物代码': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=2, max_size=10)),
        '客户代码': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=2, max_size=10)),
        '运输代码': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=2, max_size=10))
    }


@st.composite
def valid_csv_content(draw):
    """生成有效的CSV内容"""
    num_rows = draw(st.integers(min_value=1, max_value=50))
    rows = [draw(valid_manifest_row()) for _ in range(num_rows)]
    
    # 确保快递单号唯一
    tracking_numbers = set()
    for row in rows:
        base_tracking = row['快递单号']
        counter = 0
        while row['快递单号'] in tracking_numbers:
            counter += 1
            row['快递单号'] = f"{base_tracking}{counter}"
        tracking_numbers.add(row['快递单号'])
    
    df = pd.DataFrame(rows)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue().encode('utf-8')


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def csv_processor():
    """创建CSV处理器实例"""
    return CSVProcessor()


@pytest.fixture
def data_validator():
    """创建数据验证器实例"""
    return DataValidator()


@pytest.fixture
def manifest_storage(test_db):
    """创建清单存储器实例"""
    return ManifestStorage(test_db)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=valid_csv_content())
def test_save_mode_persists_valid_records(csv_content, csv_processor, data_validator, manifest_storage, test_db):
    """
    属性7：保存模式持久化
    
    对于任何有效的CSV文件，在preview_only=false模式下处理时，
    应该将有效记录持久化到数据库
    """
    # 获取处理前的记录数
    initial_count = test_db.query(CargoManifest).count()
    
    # 在保存模式下处理文件
    result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator,
        manifest_storage=manifest_storage
    )
    
    # 获取处理后的记录数
    final_count = test_db.query(CargoManifest).count()
    
    # 如果有有效行，应该增加数据库记录
    if result.success and result.statistics.valid_rows > 0:
        expected_new_records = result.statistics.inserted
        actual_new_records = final_count - initial_count
        
        assert actual_new_records == expected_new_records, \
            f"保存模式应该插入 {expected_new_records} 条记录，但实际插入了 {actual_new_records} 条"
        
        # 断言：统计信息应该准确
        assert result.statistics.inserted > 0 or result.statistics.updated > 0, \
            "保存模式应该有插入或更新的记录"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=valid_csv_content())
def test_save_mode_returns_statistics_without_detailed_rows(csv_content, csv_processor, data_validator, manifest_storage):
    """
    属性7：保存模式持久化（统计信息）
    
    对于任何有效的CSV文件，在preview_only=false模式下处理时，
    应该返回处理统计信息，但不返回详细的行数据
    """
    # 在保存模式下处理文件
    result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator,
        manifest_storage=manifest_storage
    )
    
    # 如果处理成功
    if result.success:
        # 断言：应该有统计信息
        assert result.statistics is not None, "保存模式应该返回统计信息"
        assert hasattr(result.statistics, 'total_rows'), "统计信息应该包含总行数"
        assert hasattr(result.statistics, 'valid_rows'), "统计信息应该包含有效行数"
        assert hasattr(result.statistics, 'invalid_rows'), "统计信息应该包含无效行数"
        assert hasattr(result.statistics, 'inserted'), "统计信息应该包含插入数"
        assert hasattr(result.statistics, 'updated'), "统计信息应该包含更新数"
        
        # 断言：不应该返回详细的行数据（保存模式）
        # 注意：在保存模式下，preview_data应该为None或空
        if result.preview_data is not None:
            assert len(result.preview_data) == 0, "保存模式不应该返回详细的行数据"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=valid_csv_content())
def test_save_mode_statistics_accuracy(csv_content, csv_processor, data_validator, manifest_storage, test_db):
    """
    属性7：保存模式持久化（统计准确性）
    
    对于任何有效的CSV文件，在保存模式下处理时，
    返回的统计信息应该与实际数据库操作结果一致
    """
    # 获取处理前的记录数
    initial_count = test_db.query(CargoManifest).count()
    
    # 在保存模式下处理文件
    result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator,
        manifest_storage=manifest_storage
    )
    
    # 获取处理后的记录数
    final_count = test_db.query(CargoManifest).count()
    
    if result.success:
        # 断言：统计信息应该准确反映数据库变化
        actual_change = final_count - initial_count
        reported_change = result.statistics.inserted
        
        assert actual_change == reported_change, \
            f"统计信息报告插入 {reported_change} 条，但数据库实际增加 {actual_change} 条"
        
        # 断言：总行数应该等于有效行数加无效行数
        assert result.statistics.total_rows == result.statistics.valid_rows + result.statistics.invalid_rows, \
            "总行数应该等于有效行数加无效行数"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
