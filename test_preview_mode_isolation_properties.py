"""
属性测试：预览模式隔离
**Feature: csv-file-upload, Property 6: Preview Mode Isolation**
**Validates: Requirements 3.1, 3.3**

测试预览模式不会对数据库进行任何修改
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
def test_preview_mode_does_not_persist_data(csv_content, csv_processor, data_validator, manifest_storage, test_db):
    """
    属性6：预览模式隔离
    
    对于任何有效的CSV文件，在preview_only=true模式下处理时，
    不应该向数据库中插入任何记录
    """
    # 获取处理前的记录数
    initial_count = test_db.query(CargoManifest).count()
    
    # 在预览模式下处理文件
    result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=data_validator,
        manifest_storage=manifest_storage
    )
    
    # 获取处理后的记录数
    final_count = test_db.query(CargoManifest).count()
    
    # 断言：预览模式不应该改变数据库记录数
    assert initial_count == final_count, \
        f"预览模式不应该修改数据库，但记录数从 {initial_count} 变为 {final_count}"
    
    # 断言：预览模式应该返回预览数据
    if result.success and result.statistics.valid_rows > 0:
        assert result.preview_data is not None, "预览模式应该返回预览数据"
        assert len(result.preview_data) > 0, "预览数据不应该为空"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=valid_csv_content())
def test_preview_mode_returns_detailed_row_information(csv_content, csv_processor, data_validator, manifest_storage):
    """
    属性6：预览模式隔离（详细信息）
    
    对于任何有效的CSV文件，在preview_only=true模式下处理时，
    应该返回详细的行信息，包括行号、数据、验证状态和错误信息
    """
    # 在预览模式下处理文件
    result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=data_validator,
        manifest_storage=manifest_storage
    )
    
    # 如果处理成功且有有效行
    if result.success and result.statistics.total_rows > 0:
        # 断言：应该有预览数据
        assert result.preview_data is not None, "预览模式应该返回预览数据"
        
        # 断言：预览数据应该包含详细信息
        for preview_row in result.preview_data:
            assert hasattr(preview_row, 'row_number'), "预览行应该包含行号"
            assert hasattr(preview_row, 'data'), "预览行应该包含数据"
            assert hasattr(preview_row, 'valid'), "预览行应该包含验证状态"
            assert hasattr(preview_row, 'errors'), "预览行应该包含错误信息"
            
            # 断言：行号应该大于0
            assert preview_row.row_number > 0, "行号应该大于0"
            
            # 断言：数据应该是字典
            assert isinstance(preview_row.data, dict), "数据应该是字典"
            
            # 断言：验证状态应该是布尔值
            assert isinstance(preview_row.valid, bool), "验证状态应该是布尔值"
            
            # 断言：错误信息应该是列表
            assert isinstance(preview_row.errors, list), "错误信息应该是列表"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
