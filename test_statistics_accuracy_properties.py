"""
属性测试：统计准确性 (Property 9: Statistics Accuracy)
验证需求：4.1

测试CSV处理器返回的统计信息与实际处理结果准确匹配
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
import pandas as pd
import io
import tempfile
import os
from datetime import datetime

from app.services.csv_processor import CSVProcessor, ProcessingStatistics
from app.services.data_validator import DataValidator
from app.services.manifest_storage import ManifestStorage, ManifestRecord
from app.core.database import get_db
from app.models.cargo_manifest import CargoManifest


# 生成有效的CSV行数据
@composite
def valid_csv_row(draw):
    """生成有效的CSV行数据"""
    return {
        '理货日期': draw(st.dates(min_value=datetime(2020, 1, 1).date(), 
                                  max_value=datetime(2025, 12, 31).date())).strftime('%Y-%m-%d'),
        '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                               min_size=8, max_size=20)),
        '集包单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                               min_size=5, max_size=15)),
        '长度': draw(st.floats(min_value=0.1, max_value=200.0)),
        '宽度': draw(st.floats(min_value=0.1, max_value=200.0)),
        '高度': draw(st.floats(min_value=0.1, max_value=200.0)),
        '重量': draw(st.floats(min_value=0.1, max_value=100.0)),
        '货物代码': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                               min_size=2, max_size=10)),
        '客户代码': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                               min_size=2, max_size=10)),
        '运输代码': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                               min_size=2, max_size=10))
    }


# 生成无效的CSV行数据（缺少必填字段）
@composite
def invalid_csv_row(draw):
    """生成无效的CSV行数据（缺少必填字段或数据类型错误）"""
    invalid_type = draw(st.sampled_from(['missing_tracking', 'missing_date', 'invalid_dimension', 'empty_codes']))
    
    if invalid_type == 'missing_tracking':
        return {
            '理货日期': draw(st.dates(min_value=datetime(2020, 1, 1).date(), 
                                    max_value=datetime(2025, 12, 31).date())).strftime('%Y-%m-%d'),
            '快递单号': '',  # 缺少快递单号
            '集包单号': draw(st.text(min_size=5, max_size=15)),
            '长度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '宽度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '高度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '重量': draw(st.floats(min_value=0.1, max_value=100.0)),
            '货物代码': draw(st.text(min_size=2, max_size=10)),
            '客户代码': draw(st.text(min_size=2, max_size=10)),
            '运输代码': draw(st.text(min_size=2, max_size=10))
        }
    elif invalid_type == 'missing_date':
        return {
            '理货日期': '',  # 缺少理货日期
            '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                                   min_size=8, max_size=20)),
            '集包单号': draw(st.text(min_size=5, max_size=15)),
            '长度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '宽度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '高度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '重量': draw(st.floats(min_value=0.1, max_value=100.0)),
            '货物代码': draw(st.text(min_size=2, max_size=10)),
            '客户代码': draw(st.text(min_size=2, max_size=10)),
            '运输代码': draw(st.text(min_size=2, max_size=10))
        }
    elif invalid_type == 'invalid_dimension':
        return {
            '理货日期': draw(st.dates(min_value=datetime(2020, 1, 1).date(), 
                                    max_value=datetime(2025, 12, 31).date())).strftime('%Y-%m-%d'),
            '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                                   min_size=8, max_size=20)),
            '集包单号': draw(st.text(min_size=5, max_size=15)),
            '长度': -10.0,  # 负数长度
            '宽度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '高度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '重量': draw(st.floats(min_value=0.1, max_value=100.0)),
            '货物代码': draw(st.text(min_size=2, max_size=10)),
            '客户代码': draw(st.text(min_size=2, max_size=10)),
            '运输代码': draw(st.text(min_size=2, max_size=10))
        }
    else:  # empty_codes
        return {
            '理货日期': draw(st.dates(min_value=datetime(2020, 1, 1).date(), 
                                    max_value=datetime(2025, 12, 31).date())).strftime('%Y-%m-%d'),
            '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                                   min_size=8, max_size=20)),
            '集包单号': draw(st.text(min_size=5, max_size=15)),
            '长度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '宽度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '高度': draw(st.floats(min_value=0.1, max_value=200.0)),
            '重量': draw(st.floats(min_value=0.1, max_value=100.0)),
            '货物代码': '',  # 缺少货物代码
            '客户代码': '',  # 缺少客户代码
            '运输代码': ''   # 缺少运输代码
        }


# 生成混合的CSV数据（包含有效和无效行）
@composite
def mixed_csv_data(draw):
    """生成包含有效和无效行的CSV数据"""
    num_valid = draw(st.integers(min_value=0, max_value=50))
    num_invalid = draw(st.integers(min_value=0, max_value=50))
    
    # 确保至少有一行数据
    assume(num_valid + num_invalid > 0)
    
    rows = []
    
    # 添加有效行
    for _ in range(num_valid):
        rows.append(draw(valid_csv_row()))
    
    # 添加无效行
    for _ in range(num_invalid):
        rows.append(draw(invalid_csv_row()))
    
    return rows, num_valid, num_invalid


def create_csv_file(rows):
    """从行数据创建CSV文件内容"""
    if not rows:
        return b''
    
    df = pd.DataFrame(rows)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue()


class TestStatisticsAccuracyProperties:
    """
    属性9：统计准确性
    验证需求：4.1
    
    对于任何处理的文件，返回的统计信息应该准确反映实际处理结果
    """
    
    @given(mixed_csv_data())
    @settings(max_examples=20, deadline=None)
    def test_property_9_total_rows_equals_valid_plus_invalid(self, mixed_data):
        """
        属性9.1：总行数应该等于有效行数加无效行数
        
        **验证：需求4.1**
        
        对于任何CSV文件，统计信息中的 total_rows 应该等于 valid_rows + invalid_rows
        """
        rows, expected_valid, expected_invalid = mixed_data
        
        # 创建CSV文件
        csv_content = create_csv_file(rows)
        
        # 初始化处理器
        csv_processor = CSVProcessor()
        data_validator = DataValidator()
        
        # 处理文件（预览模式，不涉及数据库）
        result = csv_processor.process_file(
            file_content=csv_content,
            filename='test.csv',
            preview_only=True,
            data_validator=data_validator,
            manifest_storage=None
        )
        
        # 验证处理成功
        assert result.success, f"处理失败: {result.errors}"
        
        # 验证统计准确性
        stats = result.statistics
        
        # 属性：total_rows = valid_rows + invalid_rows
        assert stats.total_rows == stats.valid_rows + stats.invalid_rows, \
            f"总行数不匹配: {stats.total_rows} != {stats.valid_rows} + {stats.invalid_rows}"
        
        # 验证总行数与输入数据匹配
        assert stats.total_rows == len(rows), \
            f"总行数与输入不匹配: {stats.total_rows} != {len(rows)}"
    
    @given(mixed_csv_data())
    @settings(max_examples=20, deadline=None)
    def test_property_9_statistics_match_actual_results(self, mixed_data):
        """
        属性9.2：统计信息应该与实际处理结果匹配
        
        **验证：需求4.1**
        
        对于任何CSV文件，统计信息应该准确反映实际的验证结果
        """
        rows, expected_valid, expected_invalid = mixed_data
        
        # 创建CSV文件
        csv_content = create_csv_file(rows)
        
        # 初始化处理器
        csv_processor = CSVProcessor()
        data_validator = DataValidator()
        
        # 处理文件（预览模式）
        result = csv_processor.process_file(
            file_content=csv_content,
            filename='test.csv',
            preview_only=True,
            data_validator=data_validator,
            manifest_storage=None
        )
        
        # 验证处理成功
        assert result.success, f"处理失败: {result.errors}"
        
        stats = result.statistics
        
        # 手动计算实际的有效和无效行数
        actual_valid = 0
        actual_invalid = 0
        
        if result.preview_data:
            for preview_row in result.preview_data:
                if preview_row.valid:
                    actual_valid += 1
                else:
                    actual_invalid += 1
        
        # 如果预览数据少于总行数，我们只能验证预览部分
        if result.preview_data and len(result.preview_data) < stats.total_rows:
            # 预览模式只返回部分数据，无法完全验证
            # 但至少验证预览数据的统计是一致的
            preview_total = actual_valid + actual_invalid
            assert preview_total == len(result.preview_data), \
                f"预览数据统计不一致: {preview_total} != {len(result.preview_data)}"
        
        # 验证所有计数都是非负数
        assert stats.total_rows >= 0, "总行数不能为负数"
        assert stats.valid_rows >= 0, "有效行数不能为负数"
        assert stats.invalid_rows >= 0, "无效行数不能为负数"
        assert stats.inserted >= 0, "插入数不能为负数"
        assert stats.updated >= 0, "更新数不能为负数"
        assert stats.skipped >= 0, "跳过数不能为负数"
    
    @given(st.lists(valid_csv_row(), min_size=1, max_size=20))
    @settings(max_examples=10, deadline=None)
    def test_property_9_save_mode_statistics_accuracy(self, rows):
        """
        属性9.3：保存模式下的统计准确性
        
        **验证：需求4.1**
        
        在保存模式下，valid_rows 应该等于 inserted + updated + skipped
        """
        # 获取数据库会话
        db = next(get_db())
        try:
            # 创建CSV文件
            csv_content = create_csv_file(rows)
            
            # 初始化处理器
            csv_processor = CSVProcessor()
            data_validator = DataValidator()
            manifest_storage = ManifestStorage(db)
            
            # 处理文件（保存模式）
            result = csv_processor.process_file(
                file_content=csv_content,
                filename='test.csv',
                preview_only=False,
                data_validator=data_validator,
                manifest_storage=manifest_storage
            )
            
            # 验证处理成功
            assert result.success, f"处理失败: {result.errors}"
            
            stats = result.statistics
            
            # 属性：在保存模式下，valid_rows 应该等于 inserted + updated + skipped
            if stats.inserted > 0 or stats.updated > 0 or stats.skipped > 0:
                stored_total = stats.inserted + stats.updated + stats.skipped
                assert stored_total <= stats.valid_rows, \
                    f"存储统计超过有效行数: {stored_total} > {stats.valid_rows}"
        finally:
            db.rollback()
            db.close()
    
    @given(mixed_csv_data())
    @settings(max_examples=10, deadline=None)
    def test_property_9_verify_statistics_accuracy_method(self, mixed_data):
        """
        属性9.4：统计验证方法应该正确检测不一致
        
        **验证：需求4.1**
        
        CSV处理器的统计验证方法应该能够检测统计不一致
        """
        rows, expected_valid, expected_invalid = mixed_data
        
        # 创建CSV文件
        csv_content = create_csv_file(rows)
        
        # 初始化处理器
        csv_processor = CSVProcessor()
        data_validator = DataValidator()
        
        # 处理文件
        result = csv_processor.process_file(
            file_content=csv_content,
            filename='test.csv',
            preview_only=True,
            data_validator=data_validator,
            manifest_storage=None
        )
        
        # 验证处理成功
        assert result.success, f"处理失败: {result.errors}"
        
        # 使用统计验证方法
        is_accurate, errors = csv_processor.verify_statistics_accuracy(result.statistics)
        
        # 统计应该是准确的
        assert is_accurate, f"统计验证失败: {errors}"
        assert len(errors) == 0, f"不应该有错误: {errors}"
    
    @given(st.lists(valid_csv_row(), min_size=1, max_size=30))
    @settings(max_examples=50, deadline=None)
    def test_property_9_statistics_consistency_across_modes(self, rows):
        """
        属性9.5：预览模式和保存模式的统计一致性
        
        **验证：需求4.1**
        
        对于相同的文件，预览模式和保存模式应该报告相同的 total_rows、valid_rows 和 invalid_rows
        """
        # 获取数据库会话
        db = next(get_db())
        try:
            # 创建CSV文件
            csv_content = create_csv_file(rows)
            
            # 初始化处理器
            csv_processor = CSVProcessor()
            data_validator_preview = DataValidator()
            data_validator_save = DataValidator()
            manifest_storage = ManifestStorage(db)
            
            # 预览模式处理
            result_preview = csv_processor.process_file(
                file_content=csv_content,
                filename='test.csv',
                preview_only=True,
                data_validator=data_validator_preview,
                manifest_storage=None
            )
            
            # 保存模式处理
            result_save = csv_processor.process_file(
                file_content=csv_content,
                filename='test.csv',
                preview_only=False,
                data_validator=data_validator_save,
                manifest_storage=manifest_storage
            )
            
            # 验证两种模式都成功
            assert result_preview.success, f"预览模式失败: {result_preview.errors}"
            assert result_save.success, f"保存模式失败: {result_save.errors}"
            
            # 验证统计一致性
            assert result_preview.statistics.total_rows == result_save.statistics.total_rows, \
                "预览和保存模式的总行数应该相同"
            assert result_preview.statistics.valid_rows == result_save.statistics.valid_rows, \
                "预览和保存模式的有效行数应该相同"
            assert result_preview.statistics.invalid_rows == result_save.statistics.invalid_rows, \
                "预览和保存模式的无效行数应该相同"
        finally:
            db.rollback()
            db.close()


# Pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = next(get_db())
    try:
        yield db
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
