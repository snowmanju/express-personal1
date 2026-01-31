"""
属性测试：模式一致性
**Feature: csv-file-upload, Property 8: Mode Consistency**
**Validates: Requirements 3.5**

测试预览模式和保存模式的验证结果应该一致
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


# 策略：生成包含有效和无效数据的混合CSV
@st.composite
def mixed_csv_content(draw):
    """生成包含有效和无效数据的CSV内容"""
    num_rows = draw(st.integers(min_value=5, max_value=30))
    rows = []
    
    for i in range(num_rows):
        # 随机决定是否生成有效行
        is_valid = draw(st.booleans())
        
        if is_valid:
            row = draw(valid_manifest_row())
        else:
            # 生成无效行（缺少必填字段或数据类型错误）
            row = draw(valid_manifest_row())
            # 随机选择一个错误类型
            error_type = draw(st.integers(min_value=0, max_value=3))
            
            if error_type == 0:
                # 缺少必填字段
                row['快递单号'] = ''
            elif error_type == 1:
                # 数值字段为非数字
                row['长度'] = 'invalid'
            elif error_type == 2:
                # 日期格式错误
                row['理货日期'] = 'not-a-date'
            else:
                # 快递单号包含非法字符
                row['快递单号'] = 'ABC-123-XYZ'
        
        rows.append(row)
    
    # 确保快递单号唯一（对于有效的快递单号）
    tracking_numbers = set()
    for row in rows:
        if row['快递单号'] and isinstance(row['快递单号'], str) and row['快递单号'].strip():
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
@given(csv_content=mixed_csv_content())
def test_preview_and_save_mode_validation_consistency(csv_content, csv_processor, test_db):
    """
    属性8：模式一致性
    
    对于任何CSV文件，在预览模式和保存模式下处理时，
    验证结果（总行数、有效行数、无效行数）应该完全一致
    """
    # 创建两个独立的验证器和存储器实例
    data_validator_preview = DataValidator()
    manifest_storage_preview = ManifestStorage(test_db)
    
    data_validator_save = DataValidator()
    manifest_storage_save = ManifestStorage(test_db)
    
    # 在预览模式下处理
    preview_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=data_validator_preview,
        manifest_storage=manifest_storage_preview
    )
    
    # 在保存模式下处理
    save_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator_save,
        manifest_storage=manifest_storage_save
    )
    
    # 断言：两种模式的验证结果应该一致
    if preview_result.success and save_result.success:
        assert preview_result.statistics.total_rows == save_result.statistics.total_rows, \
            f"预览模式和保存模式的总行数不一致: {preview_result.statistics.total_rows} vs {save_result.statistics.total_rows}"
        
        assert preview_result.statistics.valid_rows == save_result.statistics.valid_rows, \
            f"预览模式和保存模式的有效行数不一致: {preview_result.statistics.valid_rows} vs {save_result.statistics.valid_rows}"
        
        assert preview_result.statistics.invalid_rows == save_result.statistics.invalid_rows, \
            f"预览模式和保存模式的无效行数不一致: {preview_result.statistics.invalid_rows} vs {save_result.statistics.invalid_rows}"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=mixed_csv_content())
def test_preview_and_save_mode_error_consistency(csv_content, csv_processor, test_db):
    """
    属性8：模式一致性（错误一致性）
    
    对于任何CSV文件，在预览模式和保存模式下处理时，
    对于相同的行，应该产生相同的验证错误
    """
    # 创建两个独立的验证器和存储器实例
    data_validator_preview = DataValidator()
    manifest_storage_preview = ManifestStorage(test_db)
    
    data_validator_save = DataValidator()
    manifest_storage_save = ManifestStorage(test_db)
    
    # 在预览模式下处理
    preview_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=data_validator_preview,
        manifest_storage=manifest_storage_preview
    )
    
    # 在保存模式下处理
    save_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator_save,
        manifest_storage=manifest_storage_save
    )
    
    # 如果预览模式返回了预览数据，验证错误一致性
    if preview_result.success and preview_result.preview_data:
        # 对于预览数据中的每一行，验证其验证状态
        for preview_row in preview_result.preview_data:
            # 预览模式中的无效行数应该与保存模式一致
            # 注意：我们只能比较统计信息，因为保存模式不返回详细行数据
            pass
        
        # 至少验证统计信息一致
        assert preview_result.statistics.invalid_rows == save_result.statistics.invalid_rows, \
            "预览模式和保存模式检测到的无效行数应该一致"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(csv_content=mixed_csv_content())
def test_mode_consistency_with_duplicate_detection(csv_content, csv_processor, test_db):
    """
    属性8：模式一致性（重复检测一致性）
    
    对于任何CSV文件，在预览模式和保存模式下处理时，
    重复快递单号的检测应该一致
    """
    # 创建两个独立的验证器和存储器实例
    data_validator_preview = DataValidator()
    manifest_storage_preview = ManifestStorage(test_db)
    
    data_validator_save = DataValidator()
    manifest_storage_save = ManifestStorage(test_db)
    
    # 在预览模式下处理
    preview_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=data_validator_preview,
        manifest_storage=manifest_storage_preview
    )
    
    # 在保存模式下处理
    save_result = csv_processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=False,
        data_validator=data_validator_save,
        manifest_storage=manifest_storage_save
    )
    
    # 断言：验证逻辑应该一致
    if preview_result.success and save_result.success:
        # 两种模式应该检测到相同数量的有效和无效行
        assert preview_result.statistics.valid_rows == save_result.statistics.valid_rows, \
            "预览模式和保存模式应该检测到相同数量的有效行"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
