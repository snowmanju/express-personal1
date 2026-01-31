"""
属性测试：全面数据验证
Feature: csv-file-upload, Property 4: Comprehensive Data Validation
验证需求: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
import pandas as pd
from datetime import datetime, date
from hypothesis import given, strategies as st, assume, settings
from app.services.data_validator import DataValidator, RowValidationResult


class TestComprehensiveDataValidationProperties:
    """全面数据验证属性测试类"""

    def setup_method(self):
        """测试前设置"""
        self.validator = DataValidator()
        self.validator.reset_duplicate_check()  # 重置重复检查状态

    @given(
        tracking_number=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        manifest_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        transport_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        customer_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        goods_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        length=st.one_of(st.none(), st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False)),
        width=st.one_of(st.none(), st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False)),
        height=st.one_of(st.none(), st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False)),
        weight=st.one_of(st.none(), st.floats(min_value=0.001, max_value=999999.999, allow_nan=False, allow_infinity=False))
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_row_data_passes_all_validations(self, tracking_number, manifest_date, transport_code,
                                                    customer_code, goods_code, length, width, height, weight):
        """
        属性4：全面数据验证 - 有效数据通过所有验证
        
        对于任何包含所有必需字段且格式正确的CSV行，DataValidator应该验证通过
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        # 重置重复检查以避免干扰
        self.validator.reset_duplicate_check()
        
        # 确保必填字段非空
        assume(tracking_number.strip() != "")
        assume(transport_code.strip() != "")
        assume(customer_code.strip() != "")
        assume(goods_code.strip() != "")
        
        # 构造有效的行数据
        row_data = {
            '快递单号': tracking_number,
            '理货日期': manifest_date.strftime('%Y-%m-%d'),
            '运输代码': transport_code,
            '客户代码': customer_code,
            '货物代码': goods_code
        }
        
        # 添加可选的数值字段
        if length is not None:
            row_data['长度'] = length
        if width is not None:
            row_data['宽度'] = width
        if height is not None:
            row_data['高度'] = height
        if weight is not None:
            row_data['重量'] = weight
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：有效数据应该通过验证
        assert isinstance(result, RowValidationResult), "应该返回RowValidationResult对象"
        assert result.is_valid, f"有效数据应该通过验证，但失败了: {result.errors}"
        assert len(result.errors) == 0, f"有效数据不应该有错误: {result.errors}"
        assert result.row_number == 1, "行号应该正确"

    @given(
        missing_field=st.sampled_from(['快递单号', '理货日期', '运输代码', '客户代码', '货物代码'])
    )
    @settings(max_examples=50, deadline=None)
    def test_missing_required_field_fails_validation(self, missing_field):
        """
        属性4：全面数据验证 - 缺失必填字段导致验证失败
        
        对于任何缺少必填字段的CSV行，DataValidator应该检测到并返回错误
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.1, 2.5**
        """
        # 构造完整的行数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 移除指定的必填字段
        del row_data[missing_field]
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：缺失必填字段应该导致验证失败
        assert not result.is_valid, f"缺失必填字段 {missing_field} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        assert any(missing_field in error for error in result.errors), \
            f"错误信息应该提到缺失的字段 {missing_field}，但错误是: {result.errors}"

    @given(
        field_name=st.sampled_from(['快递单号', '理货日期', '运输代码', '客户代码', '货物代码']),
        empty_value=st.sampled_from(['', '   ', '\t', '\n'])
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_required_field_fails_validation(self, field_name, empty_value):
        """
        属性4：全面数据验证 - 空的必填字段导致验证失败
        
        对于任何必填字段为空的CSV行，DataValidator应该检测到并返回错误
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.1, 2.5**
        """
        # 构造完整的行数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 设置指定字段为空值
        row_data[field_name] = empty_value
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：空的必填字段应该导致验证失败
        assert not result.is_valid, f"空的必填字段 {field_name} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        assert any(field_name in error and '不能为空' in error for error in result.errors), \
            f"错误信息应该提到字段 {field_name} 不能为空，但错误是: {result.errors}"

    @given(
        dimension_field=st.sampled_from(['长度', '宽度', '高度', '重量']),
        invalid_value=st.one_of(
            st.text(min_size=1, max_size=10, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'),
            st.floats(min_value=-1000, max_value=-0.01, allow_nan=False, allow_infinity=False),
            st.just('invalid')
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_numeric_dimension_fails_validation(self, dimension_field, invalid_value):
        """
        属性4：全面数据验证 - 无效的数值字段导致验证失败
        
        对于任何数值字段包含非数值或负数的CSV行，DataValidator应该检测到并返回错误
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.2, 2.5**
        """
        # 构造基础有效数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001',
            dimension_field: invalid_value
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：无效的数值字段应该导致验证失败
        assert not result.is_valid, f"无效的数值字段 {dimension_field}={invalid_value} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        # 检查错误信息是否提到该字段
        assert any(dimension_field in error for error in result.errors), \
            f"错误信息应该提到字段 {dimension_field}，但错误是: {result.errors}"

    @given(
        invalid_date=st.one_of(
            st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'),
            st.just('2024-13-01'),  # 无效月份
            st.just('2024-02-30'),  # 无效日期
            st.just('invalid-date'),
            st.just('99/99/9999')
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_date_format_fails_validation(self, invalid_date):
        """
        属性4：全面数据验证 - 无效的日期格式导致验证失败
        
        对于任何理货日期格式不正确的CSV行，DataValidator应该检测到并返回错误
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.3, 2.5**
        """
        # 构造基础有效数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': invalid_date,
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：无效的日期格式应该导致验证失败
        assert not result.is_valid, f"无效的日期格式 {invalid_date} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        assert any('理货日期' in error and '格式' in error for error in result.errors), \
            f"错误信息应该提到理货日期格式错误，但错误是: {result.errors}"

    @given(
        invalid_tracking=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Lu', 'Ll', 'Nd'),  # 排除字母和数字
            min_codepoint=33, max_codepoint=126  # 可打印ASCII字符
        )).filter(lambda x: x.strip() != '' and not x.isalnum())
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_tracking_number_format_fails_validation(self, invalid_tracking):
        """
        属性4：全面数据验证 - 无效的快递单号格式导致验证失败
        
        对于任何快递单号包含非字母数字字符的CSV行，DataValidator应该检测到并返回错误
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.4, 2.5**
        """
        # 重置重复检查以避免干扰
        self.validator.reset_duplicate_check()
        
        # 构造基础有效数据
        row_data = {
            '快递单号': invalid_tracking,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：无效的快递单号格式应该导致验证失败
        assert not result.is_valid, f"无效的快递单号格式 {repr(invalid_tracking)} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        assert any('快递单号' in error for error in result.errors), \
            f"错误信息应该提到快递单号，但错误是: {result.errors}"

    @given(
        valid_date_format=st.sampled_from(['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']),
        date_value=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
    )
    @settings(max_examples=50, deadline=None)
    def test_various_valid_date_formats_pass_validation(self, valid_date_format, date_value):
        """
        属性4：全面数据验证 - 各种有效日期格式通过验证
        
        对于任何使用支持的日期格式的CSV行，DataValidator应该验证通过
        
        **Feature: csv-file-upload, Property 4: Comprehensive Data Validation**
        **验证需求: Requirements 2.3**
        """
        # 重置重复检查以避免干扰
        self.validator.reset_duplicate_check()
        
        # 构造基础有效数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': date_value.strftime(valid_date_format),
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：有效的日期格式应该通过验证
        assert result.is_valid, f"有效的日期格式 {date_value.strftime(valid_date_format)} 应该通过验证，但失败了: {result.errors}"
        assert len(result.errors) == 0, f"有效的日期格式不应该有错误: {result.errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
