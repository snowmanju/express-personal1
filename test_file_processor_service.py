"""
文件处理服务测试
"""

import pytest
import pandas as pd
import io
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from app.services.file_processor_service import FileProcessorService
from app.models.cargo_manifest import CargoManifest


class TestFileProcessorService:
    """文件处理服务测试类"""

    def setup_method(self):
        """测试前设置"""
        self.mock_db = Mock()
        self.service = FileProcessorService(db=self.mock_db)

    def test_validate_file_format_valid_formats(self):
        """测试有效文件格式验证"""
        assert self.service.validate_file_format("test.csv") == True
        assert self.service.validate_file_format("test.xlsx") == True
        assert self.service.validate_file_format("test.xls") == True
        assert self.service.validate_file_format("TEST.CSV") == True

    def test_validate_file_format_invalid_formats(self):
        """测试无效文件格式验证"""
        assert self.service.validate_file_format("test.txt") == False
        assert self.service.validate_file_format("test.pdf") == False
        assert self.service.validate_file_format("test") == False
        assert self.service.validate_file_format("") == False
        assert self.service.validate_file_format(None) == False

    def test_parse_csv_file_success(self):
        """测试CSV文件解析成功"""
        csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\nTEST001,2024-01-01,T001,C001,G001"
        file_bytes = csv_content.encode('utf-8')
        
        df, errors = self.service.parse_file(file_bytes, "test.csv")
        
        assert len(errors) == 0
        assert len(df) == 1
        assert df.iloc[0]['快递单号'] == 'TEST001'

    def test_parse_csv_file_with_gbk_encoding(self):
        """测试GBK编码的CSV文件解析"""
        csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\nTEST001,2024-01-01,T001,C001,G001"
        file_bytes = csv_content.encode('gbk')
        
        df, errors = self.service.parse_file(file_bytes, "test.csv")
        
        assert len(errors) == 0
        assert len(df) == 1

    def test_parse_file_invalid_format(self):
        """测试不支持的文件格式"""
        file_bytes = b"test content"
        
        df, errors = self.service.parse_file(file_bytes, "test.txt")
        
        assert len(errors) == 1
        assert "不支持的文件格式" in errors[0]
        assert df.empty

    def test_parse_file_empty_content(self):
        """测试空文件内容"""
        csv_content = ""
        file_bytes = csv_content.encode('utf-8')
        
        df, errors = self.service.parse_file(file_bytes, "test.csv")
        
        assert len(errors) == 1
        assert "文件内容为空" in errors[0]

    def test_validate_columns_success(self):
        """测试列验证成功"""
        df = pd.DataFrame(columns=['快递单号', '理货日期', '运输代码', '客户代码', '货物代码'])
        
        errors = self.service.validate_columns(df)
        
        assert len(errors) == 0

    def test_validate_columns_missing_required(self):
        """测试缺少必需字段"""
        df = pd.DataFrame(columns=['快递单号', '理货日期'])  # 缺少其他必需字段
        
        errors = self.service.validate_columns(df)
        
        assert len(errors) == 1
        assert "缺少必需字段" in errors[0]

    def test_validate_columns_unknown_fields(self):
        """测试包含未知字段"""
        df = pd.DataFrame(columns=['快递单号', '理货日期', '运输代码', '客户代码', '货物代码', '未知字段'])
        
        errors = self.service.validate_columns(df)
        
        assert len(errors) == 1
        assert "包含未知字段" in errors[0]

    def test_validate_row_data_success(self):
        """测试行数据验证成功"""
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        errors = self.service.validate_row_data(row_data, 0)
        
        assert len(errors) == 0

    def test_validate_row_data_missing_required(self):
        """测试缺少必需字段数据"""
        row_data = {
            '快递单号': '',  # 空值
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        errors = self.service.validate_row_data(row_data, 0)
        
        assert len(errors) == 1
        assert "快递单号 不能为空" in errors[0]

    def test_validate_row_data_invalid_tracking_number_format(self):
        """测试无效快递单号格式"""
        row_data = {
            '快递单号': 'TEST-001!',  # 包含特殊字符
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        errors = self.service.validate_row_data(row_data, 0)
        
        assert len(errors) == 1
        assert "快递单号 格式不正确" in errors[0]

    def test_validate_row_data_invalid_date_format(self):
        """测试无效日期格式"""
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024/01/01',  # 错误的日期格式
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001'
        }
        
        errors = self.service.validate_row_data(row_data, 0)
        
        assert len(errors) == 1
        assert "理货日期 日期格式不正确" in errors[0]

    def test_validate_row_data_invalid_decimal_value(self):
        """测试无效数值"""
        row_data = {
            '快递单号': 'TEST001',
            '理货日期': '2024-01-01',
            '运输代码': 'T001',
            '客户代码': 'C001',
            '货物代码': 'G001',
            '重量': 'invalid_number'
        }
        
        errors = self.service.validate_row_data(row_data, 0)
        
        assert len(errors) == 1
        assert "重量 必须是有效数字" in errors[0]

    def test_convert_to_english_fields(self):
        """测试字段名转换"""
        df = pd.DataFrame({
            '快递单号': ['TEST001'],
            '理货日期': ['2024-01-01'],
            '运输代码': ['T001'],
            '客户代码': ['C001'],
            '货物代码': ['G001'],
            '集包单号': ['PKG001']
        })
        
        df_converted = self.service.convert_to_english_fields(df)
        
        expected_columns = ['tracking_number', 'manifest_date', 'transport_code', 
                          'customer_code', 'goods_code', 'package_number']
        assert list(df_converted.columns) == expected_columns
        assert df_converted.iloc[0]['tracking_number'] == 'TEST001'

    def test_validate_and_preview_success(self):
        """测试验证和预览成功"""
        csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\nTEST001,2024-01-01,T001,C001,G001"
        file_bytes = csv_content.encode('utf-8')
        
        result = self.service.validate_and_preview(file_bytes, "test.csv")
        
        assert result['success'] == True
        assert result['total_rows'] == 1
        assert result['valid_rows'] == 1
        assert result['invalid_rows'] == 0
        assert len(result['preview_data']) == 1
        assert result['preview_data'][0]['valid'] == True

    def test_validate_and_preview_with_errors(self):
        """测试验证和预览包含错误"""
        csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\n,2024-01-01,T001,C001,G001"  # 空快递单号
        file_bytes = csv_content.encode('utf-8')
        
        result = self.service.validate_and_preview(file_bytes, "test.csv")
        
        assert result['success'] == False
        assert result['total_rows'] == 1
        assert result['valid_rows'] == 0
        assert result['invalid_rows'] == 1
        assert len(result['preview_data']) == 1
        assert result['preview_data'][0]['valid'] == False

    @patch('app.services.file_processor_service.get_db')
    def test_process_upload_success(self, mock_get_db):
        """测试文件上传处理成功"""
        # 模拟数据库查询返回None（不存在记录）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\nTEST001,2024-01-01,T001,C001,G001"
        file_bytes = csv_content.encode('utf-8')
        
        result = self.service.process_upload(file_bytes, "test.csv")
        
        assert result['success'] == True
        assert result['total'] == 1
        assert result['inserted'] == 1
        assert result['updated'] == 0
        assert result['skipped'] == 0

    def test_process_upload_without_db(self):
        """测试没有数据库会话的上传处理"""
        service = FileProcessorService()  # 没有传入db
        
        with pytest.raises(ValueError, match="数据库会话未初始化"):
            service.process_upload(b"test", "test.csv")


if __name__ == "__main__":
    pytest.main([__file__])