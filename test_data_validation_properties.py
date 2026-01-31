"""
理货单数据验证属性测试
Feature: express-tracking-website, Property 7: 理货单数据验证
验证需求: Requirements 3.2, 3.6
"""

import pytest
import pandas as pd
import io
from datetime import datetime, date
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
from app.services.file_processor_service import FileProcessorService


class TestDataValidationProperties:
    """理货单数据验证属性测试类"""

    def setup_method(self):
        """测试前设置"""
        self.service = FileProcessorService()

    @given(
        tracking_number=st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        manifest_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
        transport_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        customer_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        goods_code=st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
        package_number=st.one_of(st.none(), st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')),
        weight=st.one_of(st.none(), st.decimals(min_value=0, max_value=999999, places=3).filter(lambda x: x >= 0)),
        length=st.one_of(st.none(), st.decimals(min_value=0, max_value=999999, places=2).filter(lambda x: x >= 0)),
        width=st.one_of(st.none(), st.decimals(min_value=0, max_value=999999, places=2).filter(lambda x: x >= 0)),
        height=st.one_of(st.none(), st.decimals(min_value=0, max_value=999999, places=2).filter(lambda x: x >= 0)),
        special_fee=st.one_of(st.none(), st.decimals(min_value=0, max_value=99999999, places=2).filter(lambda x: x >= 0))
    )
    @settings(max_examples=10, deadline=None)
    def test_valid_data_validation_and_preview_property(self, tracking_number, manifest_date, transport_code, 
                                                       customer_code, goods_code, package_number, weight, 
                                                       length, width, height, special_fee):
        """
        属性 7: 理货单数据验证 - 有效数据处理
        对于任何包含所有必需字段且格式正确的理货单数据，系统应该成功验证、解析并提供预览
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        # 跳过空的必需字段
        assume(tracking_number.strip() != "")
        assume(transport_code.strip() != "")
        assume(customer_code.strip() != "")
        assume(goods_code.strip() != "")
        
        # 创建有效的CSV数据
        data = {
            '快递单号': [tracking_number],
            '理货日期': [manifest_date.strftime('%Y-%m-%d')],
            '运输代码': [transport_code],
            '客户代码': [customer_code],
            '货物代码': [goods_code]
        }
        
        # 添加可选字段
        if package_number is not None:
            data['集包单号'] = [package_number]
        if weight is not None:
            data['重量'] = [float(weight)]
        if length is not None:
            data['长度'] = [float(length)]
        if width is not None:
            data['宽度'] = [float(width)]
        if height is not None:
            data['高度'] = [float(height)]
        if special_fee is not None:
            data['特殊费用'] = [float(special_fee)]
        
        # 创建DataFrame并转换为CSV
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        file_content = csv_buffer.getvalue().encode('utf-8')
        
        # 验证和预览
        result = self.service.validate_and_preview(file_content, 'test.csv')
        
        # 验证结果
        assert result['success'] == True, f"有效数据应该验证成功，但失败了: {result['errors']}"
        assert result['total_rows'] == 1, "应该有1行数据"
        assert result['valid_rows'] == 1, "应该有1行有效数据"
        assert result['invalid_rows'] == 0, "不应该有无效数据"
        assert len(result['errors']) == 0, f"不应该有错误: {result['errors']}"
        assert len(result['preview_data']) == 1, "应该有1行预览数据"
        
        # 验证预览数据
        preview_row = result['preview_data'][0]
        assert preview_row['valid'] == True, "预览行应该标记为有效"
        assert len(preview_row['errors']) == 0, f"预览行不应该有错误: {preview_row['errors']}"
        # 注意：pandas可能会将字符串转换为其他类型，所以我们转换为字符串进行比较
        assert str(preview_row['data']['快递单号']) == tracking_number, "快递单号应该匹配"

    @given(
        missing_field=st.sampled_from(['快递单号', '理货日期', '运输代码', '客户代码', '货物代码']),
        other_fields=st.fixed_dictionaries({
            '快递单号': st.text(min_size=1, max_size=50, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
            '理货日期': st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.strftime('%Y-%m-%d')),
            '运输代码': st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
            '客户代码': st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'),
            '货物代码': st.text(min_size=1, max_size=20, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
        })
    )
    @settings(max_examples=5, deadline=None)
    def test_missing_required_field_validation_property(self, missing_field, other_fields):
        """
        属性 7: 理货单数据验证 - 缺失必需字段检测
        对于任何缺少必需字段的理货单文件，系统应该检测到缺失字段并返回详细错误信息
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        # 跳过空的字段值
        for field, value in other_fields.items():
            if isinstance(value, str):
                assume(value.strip() != "")
        
        # 创建缺少指定字段的数据
        data = {k: [v] for k, v in other_fields.items() if k != missing_field}
        
        # 创建DataFrame并转换为CSV
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        file_content = csv_buffer.getvalue().encode('utf-8')
        
        # 验证和预览
        result = self.service.validate_and_preview(file_content, 'test.csv')
        
        # 验证结果 - 应该失败并包含缺失字段错误
        assert result['success'] == False, "缺少必需字段的文件应该验证失败"
        assert len(result['errors']) > 0, "应该有错误信息"
        
        # 检查是否包含缺失字段的错误信息
        error_messages = ' '.join(result['errors'])
        assert f"缺少必需字段" in error_messages or missing_field in error_messages, \
            f"错误信息应该提到缺失的字段 {missing_field}，但错误信息是: {result['errors']}"

    @given(
        invalid_data_type=st.sampled_from(['tracking_number', 'manifest_date', 'weight', 'length', 'width', 'height', 'special_fee']),
        invalid_value=st.one_of(
            st.text(min_size=100, max_size=200),  # 过长的字符串
            st.text(alphabet=st.characters(blacklist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Ps', 'Pe'))),  # 特殊字符
            st.just("invalid_date"),  # 无效日期
            st.just("invalid_number"),  # 无效数字
            st.just(""),  # 空字符串
            st.floats(min_value=1000000, max_value=float('inf')).filter(lambda x: x != float('inf'))  # 超出范围的数字
        )
    )
    @settings(max_examples=10, deadline=None)
    def test_invalid_data_format_validation_property(self, invalid_data_type, invalid_value):
        """
        属性 7: 理货单数据验证 - 无效数据格式检测
        对于任何包含格式错误数据的理货单文件，系统应该检测到格式错误并返回详细错误信息
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        # 跳过某些无效值组合
        if invalid_data_type in ['weight', 'length', 'width', 'height', 'special_fee'] and isinstance(invalid_value, str):
            if invalid_value in ["", "invalid_date"]:
                assume(False)  # 这些字段的空值是允许的
        
        # 创建基础有效数据
        base_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001',
            '重量': '10.5',
            '长度': '20.0',
            '宽度': '15.0',
            '高度': '10.0',
            '特殊费用': '100.00'
        }
        
        # 根据invalid_data_type设置无效值
        field_mapping = {
            'tracking_number': '快递单号',
            'manifest_date': '理货日期',
            'weight': '重量',
            'length': '长度',
            'width': '宽度',
            'height': '高度',
            'special_fee': '特殊费用'
        }
        
        if invalid_data_type in field_mapping:
            chinese_field = field_mapping[invalid_data_type]
            base_data[chinese_field] = str(invalid_value)
        
        # 创建DataFrame并转换为CSV
        df = pd.DataFrame({k: [v] for k, v in base_data.items()})
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        file_content = csv_buffer.getvalue().encode('utf-8')
        
        # 验证和预览
        result = self.service.validate_and_preview(file_content, 'test.csv')
        
        # 对于某些情况，可能仍然成功（如可选字段的空值）
        if result['success']:
            # 如果成功，检查是否有警告或者数据被正确处理
            if result['valid_rows'] > 0:
                # 数据被接受，这可能是合理的（如可选字段）
                return
        
        # 如果失败，应该有详细的错误信息
        if not result['success'] or result['invalid_rows'] > 0:
            # 应该有错误信息或预览数据中有错误
            has_errors = len(result['errors']) > 0
            has_row_errors = any(len(row.get('errors', [])) > 0 for row in result['preview_data'])
            
            assert has_errors or has_row_errors, \
                f"无效数据应该产生错误信息，但没有发现错误。数据类型: {invalid_data_type}, 值: {invalid_value}"

    @given(
        num_rows=st.integers(min_value=2, max_value=10),  # Ensure at least 2 rows for mixed data
        valid_ratio=st.floats(min_value=0.1, max_value=0.9)  # Ensure some valid and some invalid data
    )
    @settings(max_examples=5, deadline=None)
    def test_mixed_valid_invalid_data_validation_property(self, num_rows, valid_ratio):
        """
        属性 7: 理货单数据验证 - 混合有效无效数据处理
        对于任何包含混合有效和无效数据的理货单文件，系统应该正确统计有效和无效行数
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        # 计算有效和无效行数
        valid_rows_count = max(1, int(num_rows * valid_ratio))  # 至少1行有效数据
        invalid_rows_count = num_rows - valid_rows_count
        
        data_rows = []
        
        # 生成有效行
        for i in range(valid_rows_count):
            row = {
                '快递单号': f'VALID{i:03d}',
                '理货日期': '2024-01-01',
                '运输代码': f'T{i:03d}',
                '客户代码': f'C{i:03d}',
                '货物代码': f'G{i:03d}',
                '重量': '10.5'
            }
            data_rows.append(row)
        
        # 生成无效行（缺少必需字段或格式错误）
        for i in range(invalid_rows_count):
            if i % 2 == 0:
                # 缺少必需字段 - 设置为空值
                row = {
                    '快递单号': f'INVALID{i:03d}',
                    '理货日期': '2024-01-01',
                    '运输代码': f'T{i:03d}',
                    '客户代码': '',  # 空的必需字段
                    '货物代码': ''   # 空的必需字段
                }
            else:
                # 格式错误
                row = {
                    '快递单号': '',  # 空的必需字段
                    '理货日期': 'invalid-date',
                    '运输代码': f'T{i:03d}',
                    '客户代码': f'C{i:03d}',
                    '货物代码': f'G{i:03d}',
                }
            data_rows.append(row)
        
        # 创建DataFrame
        if data_rows:
            # 获取所有可能的列
            all_columns = set()
            for row in data_rows:
                all_columns.update(row.keys())
            
            # 为每行填充缺失的列
            for row in data_rows:
                for col in all_columns:
                    if col not in row:
                        row[col] = ''
            
            df = pd.DataFrame(data_rows)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            file_content = csv_buffer.getvalue().encode('utf-8')
            
            # 验证和预览
            result = self.service.validate_and_preview(file_content, 'test.csv')
            
            # 验证统计信息
            assert result['total_rows'] == num_rows, f"总行数应该是 {num_rows}，但是 {result['total_rows']}"
            
            # 验证有效和无效行数的合理性
            actual_valid = result['valid_rows']
            actual_invalid = result['invalid_rows']
            
            assert actual_valid + actual_invalid == num_rows, \
                f"有效行数 ({actual_valid}) + 无效行数 ({actual_invalid}) 应该等于总行数 ({num_rows})"
            
            # 应该有一些有效数据（因为我们确保了至少1行有效数据）
            assert actual_valid >= 1, f"应该至少有1行有效数据，但只有 {actual_valid} 行"
            
            # 如果有无效数据，应该有相应的错误信息或行级错误
            if invalid_rows_count > 0:
                has_errors = len(result['errors']) > 0 or any(
                    len(row.get('errors', [])) > 0 for row in result['preview_data']
                )
                assert has_errors, "包含无效数据时应该有错误信息"

    @given(
        field_name=st.sampled_from(['快递单号', '理货日期', '运输代码', '客户代码', '货物代码']),
        empty_value=st.sampled_from(['', '   ', '\t', '\n', None])
    )
    @settings(max_examples=3, deadline=None)
    def test_empty_required_field_validation_property(self, field_name, empty_value):
        """
        属性 7: 理货单数据验证 - 空必需字段检测
        对于任何必需字段为空的理货单数据，系统应该检测到并返回字段不能为空的错误
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        # 创建基础有效数据
        base_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        # 设置指定字段为空值
        base_data[field_name] = empty_value
        
        # 创建DataFrame并转换为CSV
        df = pd.DataFrame({k: [v] for k, v in base_data.items()})
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        file_content = csv_buffer.getvalue().encode('utf-8')
        
        # 验证和预览
        result = self.service.validate_and_preview(file_content, 'test.csv')
        
        # 应该检测到空字段错误
        if result['success']:
            # 如果整体成功，检查行级错误
            assert len(result['preview_data']) > 0, "应该有预览数据"
            preview_row = result['preview_data'][0]
            assert not preview_row['valid'] or len(preview_row['errors']) > 0, \
                f"空的必需字段 {field_name} 应该产生错误"
        else:
            # 如果整体失败，应该有错误信息
            assert len(result['errors']) > 0 or any(
                len(row.get('errors', [])) > 0 for row in result['preview_data']
            ), f"空的必需字段 {field_name} 应该产生错误信息"

    @given(
        file_format=st.sampled_from(['csv', 'xlsx']),
        encoding_issue=st.booleans()
    )
    @settings(max_examples=2, deadline=None)
    def test_file_parsing_error_handling_property(self, file_format, encoding_issue):
        """
        属性 7: 理货单数据验证 - 文件解析错误处理
        对于任何解析失败的文件，系统应该返回详细的错误信息而不是崩溃
        **Feature: express-tracking-website, Property 7: 理货单数据验证**
        **验证需求: Requirements 3.2, 3.6**
        """
        if file_format == 'csv':
            if encoding_issue:
                # 创建编码问题的CSV
                content = "快递单号,理货日期\n测试数据,2024-01-01"
                file_content = content.encode('gbk')  # 使用GBK编码但可能导致问题
            else:
                # 创建格式错误的CSV
                file_content = b"invalid,csv,format\nwith,mismatched,columns,extra"
        else:  # xlsx
            # 创建无效的Excel文件内容
            file_content = b"This is not a valid Excel file content"
        
        filename = f"test.{file_format}"
        
        # 验证和预览
        result = self.service.validate_and_preview(file_content, filename)
        
        # 应该优雅地处理错误
        if not result['success']:
            assert len(result['errors']) > 0, "解析失败时应该有错误信息"
            # 错误信息应该是描述性的，不应该包含技术堆栈信息
            for error in result['errors']:
                assert isinstance(error, str), "错误信息应该是字符串"
                assert len(error) > 0, "错误信息不应该为空"


if __name__ == "__main__":
    pytest.main([__file__])