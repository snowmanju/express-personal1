"""
属性测试：错误分类
Feature: csv-file-upload, Property 11: Error Categorization
验证需求: Requirements 4.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from app.services.data_validator import DataValidator, RowValidationResult


class TestErrorCategorizationProperties:
    """错误分类属性测试类"""

    def setup_method(self):
        """测试前设置"""
        self.validator = DataValidator()
        self.validator.reset_duplicate_check()

    @given(
        field_name=st.sampled_from(['快递单号', '理货日期', '运输代码', '客户代码', '货物代码'])
    )
    @settings(max_examples=50, deadline=None)
    def test_missing_required_field_error_is_data_format_error(self, field_name):
        """
        属性11：错误分类 - 缺失必填字段错误属于数据格式错误
        
        对于任何缺失必填字段的错误，错误信息应该明确指出字段缺失
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造缺少指定字段的数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        del row_data[field_name]
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有明确的数据格式错误
        assert not result.is_valid, "缺失必填字段应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出字段缺失（数据格式错误）
        has_format_error = any(
            field_name in error and '不能为空' in error
            for error in result.errors
        )
        assert has_format_error, \
            f"错误信息应该明确指出 {field_name} 不能为空（数据格式错误），但错误是: {result.errors}"

    @given(
        dimension_field=st.sampled_from(['长度', '宽度', '高度', '重量']),
        invalid_value=st.one_of(
            st.text(min_size=1, max_size=10, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'),
            st.just('invalid')
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_data_type_error_is_data_format_error(self, dimension_field, invalid_value):
        """
        属性11：错误分类 - 无效数据类型错误属于数据格式错误
        
        对于任何数据类型不匹配的错误，错误信息应该明确指出类型问题
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造包含无效数据类型的数据
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
        
        # 断言：应该有明确的数据格式错误
        assert not result.is_valid, f"无效的数据类型应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出数据类型问题（数据格式错误）
        has_format_error = any(
            dimension_field in error and ('数字' in error or '格式' in error)
            for error in result.errors
        )
        assert has_format_error, \
            f"错误信息应该明确指出 {dimension_field} 的数据类型问题（数据格式错误），但错误是: {result.errors}"

    @given(
        tracking_number=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    )
    @settings(max_examples=50, deadline=None)
    def test_duplicate_tracking_number_error_is_business_rule_violation(self, tracking_number):
        """
        属性11：错误分类 - 重复快递单号错误属于业务规则违反
        
        对于任何重复快递单号的错误，错误信息应该明确指出重复问题
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 确保快递单号非空
        assume(tracking_number.strip() != "")
        
        # 第一次验证（应该成功）
        row_data_1 = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        result_1 = self.validator.validate_row(row_data_1, 1)
        assert result_1.is_valid, "第一次应该通过验证"
        
        # 第二次验证（应该失败，重复）
        row_data_2 = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-02',
            '运输代码': 'T002',
            '客户代码': 'C002',
            '货物代码': 'G002'
        }
        result_2 = self.validator.validate_row(row_data_2, 2)
        
        # 断言：应该有明确的业务规则违反错误
        assert not result_2.is_valid, "重复的快递单号应该导致验证失败"
        assert len(result_2.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出重复问题（业务规则违反）
        has_business_rule_error = any(
            '重复' in error and tracking_number in error
            for error in result_2.errors
        )
        assert has_business_rule_error, \
            f"错误信息应该明确指出快递单号重复（业务规则违反），但错误是: {result_2.errors}"

    @given(
        invalid_date=st.one_of(
            st.just('invalid-date'),
            st.just('2024-13-01'),
            st.just('99/99/9999')
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_invalid_date_format_error_is_data_format_error(self, invalid_date):
        """
        属性11：错误分类 - 无效日期格式错误属于数据格式错误
        
        对于任何日期格式不正确的错误，错误信息应该明确指出格式问题
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造包含无效日期的数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': invalid_date,
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有明确的数据格式错误
        assert not result.is_valid, f"无效的日期格式应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出日期格式问题（数据格式错误）
        has_format_error = any(
            '理货日期' in error and '格式' in error
            for error in result.errors
        )
        assert has_format_error, \
            f"错误信息应该明确指出理货日期格式问题（数据格式错误），但错误是: {result.errors}"

    @given(
        invalid_tracking=st.text(min_size=1, max_size=50, alphabet=st.characters(
            blacklist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=33, max_codepoint=126
        )).filter(lambda x: x.strip() != '' and not x.isalnum())
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_tracking_format_error_is_data_format_error(self, invalid_tracking):
        """
        属性11：错误分类 - 无效快递单号格式错误属于数据格式错误
        
        对于任何快递单号格式不正确的错误，错误信息应该明确指出格式问题
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造包含无效快递单号的数据
        row_data = {
            '快递单号': invalid_tracking,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有明确的数据格式错误
        assert not result.is_valid, f"无效的快递单号格式应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出快递单号格式问题（数据格式错误）
        has_format_error = any(
            '快递单号' in error
            for error in result.errors
        )
        assert has_format_error, \
            f"错误信息应该明确指出快递单号格式问题（数据格式错误），但错误是: {result.errors}"

    @given(
        dimension_field=st.sampled_from(['长度', '宽度', '高度', '重量']),
        negative_value=st.floats(min_value=-1000, max_value=-0.01, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_negative_dimension_error_is_business_rule_violation(self, dimension_field, negative_value):
        """
        属性11：错误分类 - 负数尺寸错误属于业务规则违反
        
        对于任何尺寸为负数的错误，错误信息应该明确指出必须为正数
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造包含负数尺寸的数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001',
            dimension_field: negative_value
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有明确的业务规则违反错误
        assert not result.is_valid, f"负数尺寸应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否明确指出必须为正数（业务规则违反）
        has_business_rule_error = any(
            dimension_field in error and '正数' in error
            for error in result.errors
        )
        assert has_business_rule_error, \
            f"错误信息应该明确指出 {dimension_field} 必须为正数（业务规则违反），但错误是: {result.errors}"

    @given(
        error_type=st.sampled_from([
            ('missing_field', '快递单号', None),
            ('invalid_type', '长度', 'invalid'),
            ('invalid_date', '理货日期', 'invalid-date'),
            ('negative_value', '重量', -10.5)
        ])
    )
    @settings(max_examples=50, deadline=None)
    def test_error_messages_are_descriptive_and_specific(self, error_type):
        """
        属性11：错误分类 - 错误信息具有描述性和特定性
        
        对于任何验证错误，错误信息应该清晰描述问题并指出具体字段
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        error_category, field_name, field_value = error_type
        
        # 构造基础数据
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 根据错误类型修改数据
        if error_category == 'missing_field':
            del row_data[field_name]
        elif error_category in ['invalid_type', 'invalid_date', 'negative_value']:
            row_data[field_name] = field_value
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有错误信息
        assert not result.is_valid, f"错误类型 {error_category} 应该导致验证失败"
        assert len(result.errors) > 0, "应该有错误信息"
        
        # 检查错误信息是否包含字段名
        has_field_name = any(field_name in error for error in result.errors)
        assert has_field_name, \
            f"错误信息应该包含字段名 {field_name}，但错误是: {result.errors}"
        
        # 检查错误信息是否是字符串且非空
        for error in result.errors:
            assert isinstance(error, str), "错误信息应该是字符串"
            assert len(error) > 0, "错误信息不应该为空"
            assert len(error) < 200, "错误信息不应该过长"

    def test_multiple_errors_are_all_reported(self):
        """
        属性11：错误分类 - 多个错误都被报告
        
        对于任何包含多个验证错误的行，所有错误都应该被报告
        
        **Feature: csv-file-upload, Property 11: Error Categorization**
        **验证需求: Requirements 4.5**
        """
        # 重置状态
        self.validator.reset_duplicate_check()
        
        # 构造包含多个错误的数据
        row_data = {
            '快递单号': '',  # 错误1：空的必填字段
            '理货日期': 'invalid-date',  # 错误2：无效日期格式
            '运输代码': 'T001',
            '客户代码': '',  # 错误3：空的必填字段
            '货物代码': 'G001',
            '长度': 'invalid'  # 错误4：无效数据类型
        }
        
        # 验证行数据
        result = self.validator.validate_row(row_data, 1)
        
        # 断言：应该有多个错误信息
        assert not result.is_valid, "包含多个错误的行应该验证失败"
        assert len(result.errors) >= 3, \
            f"应该报告至少3个错误（快递单号、客户代码、理货日期或长度），但只有 {len(result.errors)} 个: {result.errors}"
        
        # 检查是否包含不同类型的错误
        error_text = ' '.join(result.errors)
        assert '快递单号' in error_text or '客户代码' in error_text, \
            "应该包含必填字段错误"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
