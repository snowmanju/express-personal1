"""
属性测试：错误恢复
**Feature: csv-file-upload, Property 5: Error Resilience**
**Validates: Requirements 2.6, 4.2, 4.3**

测试CSV处理器在遇到部分无效行时的错误恢复能力
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import io
from app.services.csv_processor import CSVProcessor
from app.services.data_validator import DataValidator
from app.services.manifest_storage import ManifestStorage


# 生成有效的行数据
@st.composite
def valid_row_data(draw):
    """生成有效的行数据"""
    return {
        '理货日期': draw(st.sampled_from(['2024-01-15', '2024/02/20', '03/15/2024'])),
        '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=5, max_size=20)),
        '集包单号': draw(st.text(min_size=0, max_size=20)),
        '长度': draw(st.floats(min_value=0.1, max_value=1000)),
        '宽度': draw(st.floats(min_value=0.1, max_value=1000)),
        '高度': draw(st.floats(min_value=0.1, max_value=1000)),
        '重量': draw(st.floats(min_value=0.1, max_value=1000)),
        '货物代码': draw(st.text(min_size=1, max_size=10)),
        '客户代码': draw(st.text(min_size=1, max_size=10)),
        '运输代码': draw(st.text(min_size=1, max_size=10))
    }


# 生成无效的行数据（缺少必填字段）
@st.composite
def invalid_row_data(draw):
    """生成无效的行数据（缺少必填字段或数据类型错误）"""
    invalid_type = draw(st.sampled_from(['missing_required', 'invalid_type', 'invalid_format']))
    
    if invalid_type == 'missing_required':
        # 缺少必填字段
        return {
            '理货日期': '',
            '快递单号': '',
            '集包单号': draw(st.text(min_size=0, max_size=20)),
            '长度': draw(st.floats(min_value=0.1, max_value=1000)),
            '宽度': draw(st.floats(min_value=0.1, max_value=1000)),
            '高度': draw(st.floats(min_value=0.1, max_value=1000)),
            '重量': draw(st.floats(min_value=0.1, max_value=1000)),
            '货物代码': '',
            '客户代码': '',
            '运输代码': ''
        }
    elif invalid_type == 'invalid_type':
        # 数值字段包含非数值
        return {
            '理货日期': draw(st.sampled_from(['2024-01-15', '2024/02/20'])),
            '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=5, max_size=20)),
            '集包单号': draw(st.text(min_size=0, max_size=20)),
            '长度': 'invalid',
            '宽度': 'invalid',
            '高度': 'invalid',
            '重量': 'invalid',
            '货物代码': draw(st.text(min_size=1, max_size=10)),
            '客户代码': draw(st.text(min_size=1, max_size=10)),
            '运输代码': draw(st.text(min_size=1, max_size=10))
        }
    else:  # invalid_format
        # 日期格式错误
        return {
            '理货日期': 'invalid-date',
            '快递单号': draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=5, max_size=20)),
            '集包单号': draw(st.text(min_size=0, max_size=20)),
            '长度': draw(st.floats(min_value=0.1, max_value=1000)),
            '宽度': draw(st.floats(min_value=0.1, max_value=1000)),
            '高度': draw(st.floats(min_value=0.1, max_value=1000)),
            '重量': draw(st.floats(min_value=0.1, max_value=1000)),
            '货物代码': draw(st.text(min_size=1, max_size=10)),
            '客户代码': draw(st.text(min_size=1, max_size=10)),
            '运输代码': draw(st.text(min_size=1, max_size=10))
        }


@given(
    valid_rows=st.lists(valid_row_data(), min_size=1, max_size=10),
    invalid_rows=st.lists(invalid_row_data(), min_size=1, max_size=5)
)
@settings(max_examples=100, deadline=None)
def test_error_recovery_continues_processing_valid_rows(valid_rows, invalid_rows):
    """
    **Feature: csv-file-upload, Property 5: Error Resilience**
    **Validates: Requirements 2.6, 4.2, 4.3**
    
    属性：对于任何包含有效和无效行的文件，CSV处理器应该继续处理有效行
    并提供详细的错误报告
    """
    # 混合有效和无效行
    all_rows = valid_rows + invalid_rows
    
    # 确保快递单号唯一
    for i, row in enumerate(all_rows):
        if '快递单号' in row and row['快递单号']:
            row['快递单号'] = f"TN{i:06d}"
    
    # 创建CSV内容
    df = pd.DataFrame(all_rows)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_content = csv_buffer.getvalue()
    
    # 处理文件
    processor = CSVProcessor()
    validator = DataValidator()
    
    result = processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=validator,
        manifest_storage=None
    )
    
    # 验证：处理应该成功完成
    assert result.success, "处理应该成功完成，即使有无效行"
    
    # 验证：统计信息应该准确
    assert result.statistics.total_rows == len(all_rows), "总行数应该匹配"
    assert result.statistics.valid_rows > 0, "应该有有效行被处理"
    assert result.statistics.invalid_rows > 0, "应该有无效行被检测"
    assert result.statistics.valid_rows + result.statistics.invalid_rows == result.statistics.total_rows
    
    # 验证：预览数据应该包含错误信息
    if result.preview_data:
        invalid_preview_rows = [row for row in result.preview_data if not row.valid]
        assert len(invalid_preview_rows) > 0, "预览数据应该包含无效行"
        
        # 验证每个无效行都有错误信息
        for invalid_row in invalid_preview_rows:
            assert len(invalid_row.errors) > 0, "无效行应该有具体的错误信息"


@given(
    rows=st.lists(valid_row_data(), min_size=5, max_size=20)
)
@settings(max_examples=50, deadline=None)
def test_error_recovery_provides_detailed_error_messages(rows):
    """
    **Feature: csv-file-upload, Property 5: Error Resilience**
    **Validates: Requirements 4.2, 4.3**
    
    属性：对于任何验证错误，系统应该提供具体的字段级错误描述
    """
    # 故意破坏一些行的数据
    for i in range(0, len(rows), 2):
        if i < len(rows):
            # 清空必填字段
            rows[i]['快递单号'] = ''
            rows[i]['货物代码'] = ''
    
    # 确保剩余行的快递单号唯一
    for i, row in enumerate(rows):
        if row['快递单号']:
            row['快递单号'] = f"TN{i:06d}"
    
    # 创建CSV内容
    df = pd.DataFrame(rows)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_content = csv_buffer.getvalue()
    
    # 处理文件
    processor = CSVProcessor()
    validator = DataValidator()
    
    result = processor.process_file(
        file_content=csv_content,
        filename='test.csv',
        preview_only=True,
        data_validator=validator,
        manifest_storage=None
    )
    
    # 验证：应该有无效行
    assert result.statistics.invalid_rows > 0, "应该检测到无效行"
    
    # 验证：预览数据中的无效行应该有详细错误信息
    if result.preview_data:
        invalid_rows = [row for row in result.preview_data if not row.valid]
        for invalid_row in invalid_rows:
            assert len(invalid_row.errors) > 0, "无效行应该有错误信息"
            # 验证错误信息包含字段名
            error_text = ' '.join(invalid_row.errors)
            assert any(field in error_text for field in ['快递单号', '货物代码', '理货日期', '运输代码', '客户代码']), \
                "错误信息应该包含具体的字段名"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
