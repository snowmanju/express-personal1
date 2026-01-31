"""
文件格式支持属性测试
Feature: express-tracking-website, Property 6: 文件格式支持
验证需求: Requirements 3.1
"""

import pytest
import pandas as pd
import io
from hypothesis import given, strategies as st, assume, settings
from app.services.file_processor_service import FileProcessorService


class TestFileFormatProperties:
    """文件格式支持属性测试类"""

    def setup_method(self):
        """测试前设置"""
        self.service = FileProcessorService()

    @given(filename=st.text(min_size=1, max_size=50))
    @settings(max_examples=5)
    def test_file_format_validation_property(self, filename):
        """
        属性 6: 文件格式支持
        对于任何文件名，系统应该接受CSV和Excel格式，拒绝其他格式
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 跳过空字符串和只包含空白字符的文件名
        assume(filename.strip() != "")
        
        # 获取文件扩展名
        if '.' in filename:
            extension = '.' + filename.lower().split('.')[-1]
        else:
            extension = ''
        
        # 支持的格式
        supported_formats = {'.csv', '.xlsx', '.xls'}
        
        # 验证格式检查结果
        is_valid = self.service.validate_file_format(filename)
        
        if extension in supported_formats:
            # 支持的格式应该返回True
            assert is_valid == True, f"支持的格式 {extension} 应该被接受，但被拒绝了"
        else:
            # 不支持的格式应该返回False
            assert is_valid == False, f"不支持的格式 {extension} 应该被拒绝，但被接受了"

    @given(
        file_extension=st.sampled_from(['.csv', '.xlsx', '.xls']),
        base_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=5, deadline=None)
    def test_supported_format_parsing_property(self, file_extension, base_name):
        """
        属性 6: 支持格式解析能力
        对于任何支持的文件格式，系统应该能够尝试解析（即使内容可能无效）
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 跳过空的基础名称
        assume(base_name.strip() != "")
        
        filename = base_name + file_extension
        
        # 验证格式被识别为支持的格式
        assert self.service.validate_file_format(filename) == True
        
        # 创建有效的测试文件内容
        if file_extension == '.csv':
            # 创建有效的CSV内容
            csv_content = "快递单号,理货日期,运输代码,客户代码,货物代码\nTEST001,2024-01-01,T001,C001,G001"
            file_bytes = csv_content.encode('utf-8')
        else:  # .xlsx or .xls
            # 创建有效的Excel内容
            try:
                df = pd.DataFrame({
                    '快递单号': ['TEST001'],
                    '理货日期': ['2024-01-01'],
                    '运输代码': ['T001'],
                    '客户代码': ['C001'],
                    '货物代码': ['G001']
                })
                buffer = io.BytesIO()
                if file_extension == '.xlsx':
                    df.to_excel(buffer, index=False, engine='openpyxl')
                else:  # .xls
                    df.to_excel(buffer, index=False, engine='xlwt')
                file_bytes = buffer.getvalue()
            except Exception:
                # 如果Excel生成失败，跳过这个测试用例
                assume(False)
        
        # 尝试解析文件
        parsed_df, errors = self.service.parse_file(file_bytes, filename)
        
        # 对于支持的格式，应该能够成功解析或返回具体的解析错误（而不是格式不支持错误）
        if errors:
            # 如果有错误，不应该是格式不支持的错误
            for error in errors:
                assert "不支持的文件格式" not in error, f"支持的格式 {file_extension} 不应该返回格式不支持错误"
        else:
            # 如果没有错误，应该成功解析出数据
            assert not parsed_df.empty, f"支持的格式 {file_extension} 应该能够解析出数据"

    @given(
        file_extension=st.text(min_size=1, max_size=10).filter(
            lambda x: x not in ['csv', 'xlsx', 'xls'] and '.' not in x
        ),
        base_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=5)
    def test_unsupported_format_rejection_property(self, file_extension, base_name):
        """
        属性 6: 不支持格式拒绝
        对于任何不支持的文件格式，系统应该拒绝并返回格式错误
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 跳过空的基础名称和扩展名
        assume(base_name.strip() != "")
        assume(file_extension.strip() != "")
        
        filename = base_name + '.' + file_extension
        
        # 验证格式被识别为不支持的格式
        assert self.service.validate_file_format(filename) == False
        
        # 尝试解析文件（使用任意内容）
        file_bytes = b"test content"
        parsed_df, errors = self.service.parse_file(file_bytes, filename)
        
        # 应该返回格式不支持的错误
        assert len(errors) > 0, "不支持的格式应该返回错误"
        assert any("不支持的文件格式" in error for error in errors), "应该包含格式不支持的错误信息"
        assert parsed_df.empty, "不支持的格式不应该返回任何数据"

    @given(
        supported_format=st.sampled_from(['csv', 'xlsx', 'xls']),
        case_variation=st.sampled_from(['lower', 'upper', 'mixed'])
    )
    @settings(max_examples=2)
    def test_case_insensitive_format_recognition_property(self, supported_format, case_variation):
        """
        属性 6: 大小写不敏感格式识别
        对于任何支持的文件格式，系统应该不区分大小写地识别格式
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 根据case_variation调整格式大小写
        if case_variation == 'lower':
            format_ext = supported_format.lower()
        elif case_variation == 'upper':
            format_ext = supported_format.upper()
        else:  # mixed
            format_ext = ''.join(c.upper() if i % 2 == 0 else c.lower() 
                               for i, c in enumerate(supported_format))
        
        filename = f"test.{format_ext}"
        
        # 无论大小写如何，都应该被识别为支持的格式
        assert self.service.validate_file_format(filename) == True, \
            f"格式 {format_ext} 应该被识别为支持的格式（大小写不敏感）"

    @given(filename=st.just(""))
    @settings(max_examples=5)
    def test_empty_filename_rejection_property(self, filename):
        """
        属性 6: 空文件名拒绝
        对于空文件名，系统应该拒绝
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 空文件名应该被拒绝
        assert self.service.validate_file_format(filename) == False, "空文件名应该被拒绝"

    @given(filename=st.text(min_size=1, max_size=50).filter(lambda x: '.' not in x))
    @settings(max_examples=3)
    def test_no_extension_rejection_property(self, filename):
        """
        属性 6: 无扩展名文件拒绝
        对于任何没有扩展名的文件名，系统应该拒绝
        **Feature: express-tracking-website, Property 6: 文件格式支持**
        **验证需求: Requirements 3.1**
        """
        # 跳过空字符串
        assume(filename.strip() != "")
        
        # 没有扩展名的文件应该被拒绝
        assert self.service.validate_file_format(filename) == False, \
            f"没有扩展名的文件 '{filename}' 应该被拒绝"


if __name__ == "__main__":
    pytest.main([__file__])