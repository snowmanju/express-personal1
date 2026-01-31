"""
属性测试：重复检测
Feature: csv-file-upload, Property 10: Duplicate Detection
验证需求: Requirements 4.4
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from app.services.data_validator import DataValidator, RowValidationResult


class TestDuplicateDetectionProperties:
    """重复检测属性测试类"""

    def setup_method(self):
        """测试前设置"""
        self.validator = DataValidator()
        self.validator.reset_duplicate_check()
    
    def teardown_method(self):
        """测试后清理"""
        if hasattr(self, 'validator'):
            self.validator.reset_duplicate_check()

    @given(
        tracking_number=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    )
    @settings(max_examples=100, deadline=None)
    def test_duplicate_tracking_numbers_detected(self, tracking_number):
        """
        属性10：重复检测 - 重复的快递单号被检测
        
        对于任何在同一文件中出现两次的快递单号，DataValidator应该在第二次出现时检测到重复
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        # 重置状态以确保测试隔离
        self.validator.reset_duplicate_check()
        
        # 确保快递单号非空
        assume(tracking_number.strip() != "")
        
        # 构造第一行数据
        row_data_1 = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 第一次验证应该成功
        result_1 = self.validator.validate_row(row_data_1, 1)
        assert result_1.is_valid, f"第一次出现的快递单号应该通过验证，但失败了: {result_1.errors}"
        assert len(result_1.errors) == 0, f"第一次出现不应该有错误: {result_1.errors}"
        
        # 构造第二行数据（相同的快递单号）
        row_data_2 = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-02',
            '运输代码': 'T002',
            '客户代码': 'C002',
            '货物代码': 'G002'
        }
        
        # 第二次验证应该失败（检测到重复）
        result_2 = self.validator.validate_row(row_data_2, 2)
        assert not result_2.is_valid, f"重复的快递单号应该被检测到，但验证通过了"
        assert len(result_2.errors) > 0, "重复的快递单号应该有错误信息"
        assert any('重复' in error for error in result_2.errors), \
            f"错误信息应该提到重复，但错误是: {result_2.errors}"
        assert any(tracking_number in error for error in result_2.errors), \
            f"错误信息应该包含快递单号 {tracking_number}，但错误是: {result_2.errors}"

    @given(
        tracking_numbers=st.lists(
            st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
            min_size=2,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_unique_tracking_numbers_pass_validation(self, tracking_numbers):
        """
        属性10：重复检测 - 唯一的快递单号通过验证
        
        对于任何包含唯一快递单号的行列表，DataValidator应该全部验证通过
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        # 重置状态以确保测试隔离
        self.validator.reset_duplicate_check()
        
        # 确保所有快递单号非空
        tracking_numbers = [tn for tn in tracking_numbers if tn.strip() != ""]
        assume(len(tracking_numbers) >= 2)
        
        # 验证每一行
        for idx, tracking_number in enumerate(tracking_numbers, start=1):
            row_data = {
                '快递单号': tracking_number,
                '理货日期': '2024-01-01',
                '运输代码': f'T{idx:03d}',
                '客户代码': f'C{idx:03d}',
                '货物代码': f'G{idx:03d}'
            }
            
            result = self.validator.validate_row(row_data, idx)
            assert result.is_valid, \
                f"唯一的快递单号 {tracking_number} 应该通过验证，但失败了: {result.errors}"
            assert len(result.errors) == 0, \
                f"唯一的快递单号不应该有错误: {result.errors}"

    @given(
        base_tracking=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        num_duplicates=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_duplicates_all_detected(self, base_tracking, num_duplicates):
        """
        属性10：重复检测 - 多次重复都被检测
        
        对于任何快递单号出现多次，DataValidator应该在每次重复出现时都检测到
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        # 重置状态以确保测试隔离
        self.validator.reset_duplicate_check()
        
        # 确保快递单号非空
        assume(base_tracking.strip() != "")
        
        # 第一次出现应该成功
        row_data_1 = {
            '快递单号': base_tracking,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        result_1 = self.validator.validate_row(row_data_1, 1)
        assert result_1.is_valid, f"第一次出现应该通过验证，但失败了: {result_1.errors}"
        
        # 后续的重复出现都应该被检测到
        for i in range(2, num_duplicates + 1):
            row_data = {
                '快递单号': base_tracking,
                '理货日期': f'2024-01-{i:02d}',
                '运输代码': f'T{i:03d}',
                '客户代码': f'C{i:03d}',
                '货物代码': f'G{i:03d}'
            }
            result = self.validator.validate_row(row_data, i)
            assert not result.is_valid, \
                f"第{i}次出现的重复快递单号应该被检测到，但验证通过了"
            assert any('重复' in error for error in result.errors), \
                f"第{i}次出现应该有重复错误，但错误是: {result.errors}"

    @given(
        tracking_numbers=st.lists(
            st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
            min_size=3,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_mixed_unique_and_duplicate_tracking_numbers(self, tracking_numbers):
        """
        属性10：重复检测 - 混合唯一和重复的快递单号
        
        对于任何包含混合唯一和重复快递单号的行列表，DataValidator应该只标记重复的
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        # 重置状态以确保测试隔离
        self.validator.reset_duplicate_check()
        
        # 确保所有快递单号非空
        tracking_numbers = [tn for tn in tracking_numbers if tn.strip() != ""]
        assume(len(tracking_numbers) >= 3)
        
        # 跟踪已见过的快递单号和预期结果
        seen = set()
        expected_results = []
        
        for tn in tracking_numbers:
            if tn in seen:
                expected_results.append(False)  # 应该失败（重复）
            else:
                expected_results.append(True)   # 应该成功（首次出现）
                seen.add(tn)
        
        # 验证每一行
        for idx, (tracking_number, expected_valid) in enumerate(zip(tracking_numbers, expected_results), start=1):
            row_data = {
                '快递单号': tracking_number,
                '理货日期': '2024-01-01',
                '运输代码': f'T{idx:03d}',
                '客户代码': f'C{idx:03d}',
                '货物代码': f'G{idx:03d}'
            }
            
            result = self.validator.validate_row(row_data, idx)
            
            if expected_valid:
                assert result.is_valid, \
                    f"首次出现的快递单号 {tracking_number} 应该通过验证，但失败了: {result.errors}"
            else:
                assert not result.is_valid, \
                    f"重复的快递单号 {tracking_number} 应该被检测到，但验证通过了"
                assert any('重复' in error for error in result.errors), \
                    f"重复的快递单号应该有重复错误，但错误是: {result.errors}"

    def test_reset_duplicate_check_clears_state(self):
        """
        属性10：重复检测 - 重置功能清除状态
        
        重置重复检查后，之前的快递单号应该可以再次使用
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        tracking_number = 'TEST001'
        
        # 第一次验证
        row_data = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        result_1 = self.validator.validate_row(row_data, 1)
        assert result_1.is_valid, "第一次应该通过验证"
        
        # 重置重复检查
        self.validator.reset_duplicate_check()
        
        # 再次验证相同的快递单号，应该成功
        result_2 = self.validator.validate_row(row_data, 1)
        assert result_2.is_valid, \
            f"重置后相同的快递单号应该通过验证，但失败了: {result_2.errors}"
        assert len(result_2.errors) == 0, \
            f"重置后不应该有重复错误: {result_2.errors}"

    @given(
        tracking_number=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        whitespace_variant=st.sampled_from(['', ' ', '  ', '\t'])
    )
    @settings(max_examples=50, deadline=None)
    def test_duplicate_detection_ignores_whitespace_differences(self, tracking_number, whitespace_variant):
        """
        属性10：重复检测 - 重复检测忽略空格差异
        
        对于任何快递单号，添加前后空格不应该绕过重复检测
        
        **Feature: csv-file-upload, Property 10: Duplicate Detection**
        **验证需求: Requirements 4.4**
        """
        # 重置状态以确保测试隔离
        self.validator.reset_duplicate_check()
        
        # 确保快递单号非空
        assume(tracking_number.strip() != "")
        
        # 第一次使用原始快递单号
        row_data_1 = {
            '快递单号': tracking_number,
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        result_1 = self.validator.validate_row(row_data_1, 1)
        assert result_1.is_valid, f"第一次应该通过验证，但失败了: {result_1.errors}"
        
        # 第二次使用带空格的快递单号
        row_data_2 = {
            '快递单号': whitespace_variant + tracking_number + whitespace_variant,
            '理货日期': '2024-01-02',
            '运输代码': 'T002',
            '客户代码': 'C002',
            '货物代码': 'G002'
        }
        result_2 = self.validator.validate_row(row_data_2, 2)
        
        # 如果空格变体去除空格后与原始相同，应该检测到重复
        if (whitespace_variant + tracking_number + whitespace_variant).strip() == tracking_number.strip():
            assert not result_2.is_valid, \
                f"带空格的重复快递单号应该被检测到，但验证通过了"
            assert any('重复' in error for error in result_2.errors), \
                f"应该有重复错误，但错误是: {result_2.errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
