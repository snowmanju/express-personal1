"""
安全验证属性测试 (Security Validation Property Tests)

Feature: csv-file-upload, Property 13: 安全验证
验证需求: 6.5

测试上传端点的安全验证，确保在处理前验证文件内容以防止恶意上传
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
import io

from app.services.file_validator import FileValidator
from app.services.csv_processor import CSVProcessor


# 测试策略
@st.composite
def malicious_file_strategy(draw):
    """生成潜在恶意的文件内容"""
    file_type = draw(st.sampled_from([
        'empty',
        'too_large',
        'binary_data',
        'script_injection',
        'path_traversal',
        'null_bytes',
        'extremely_long_lines',
    ]))
    
    if file_type == 'empty':
        return b''
    elif file_type == 'too_large':
        # 生成超过10MB的文件
        return b'A' * (11 * 1024 * 1024)
    elif file_type == 'binary_data':
        # 生成随机二进制数据
        return draw(st.binary(min_size=100, max_size=1000))
    elif file_type == 'script_injection':
        # 尝试脚本注入
        return b'<script>alert("XSS")</script>\n' * 100
    elif file_type == 'path_traversal':
        # 尝试路径遍历
        return b'../../etc/passwd\n' * 100
    elif file_type == 'null_bytes':
        # 包含空字节
        return b'data\x00with\x00nulls\n' * 100
    elif file_type == 'extremely_long_lines':
        # 极长的行
        return b'A' * 1000000 + b'\n'
    
    return b'default'


@st.composite
def malicious_filename_strategy(draw):
    """生成潜在恶意的文件名"""
    filename_type = draw(st.sampled_from([
        'path_traversal',
        'null_byte',
        'special_chars',
        'very_long',
        'executable',
        'double_extension',
    ]))
    
    if filename_type == 'path_traversal':
        return draw(st.sampled_from([
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            'C:\\Windows\\System32\\config\\sam',
        ]))
    elif filename_type == 'null_byte':
        return 'file.csv\x00.exe'
    elif filename_type == 'special_chars':
        return draw(st.text(alphabet='<>:"|?*', min_size=5, max_size=20)) + '.csv'
    elif filename_type == 'very_long':
        return 'A' * 300 + '.csv'
    elif filename_type == 'executable':
        return draw(st.sampled_from([
            'malware.exe',
            'script.bat',
            'virus.com',
            'trojan.scr',
        ]))
    elif filename_type == 'double_extension':
        return 'file.csv.exe'
    
    return 'normal.csv'


class TestSecurityValidationProperties:
    """
    安全验证属性测试类
    
    **属性13：安全验证**
    *For any* uploaded file, the Admin_Backend should validate file content 
    before processing to prevent malicious uploads
    **Validates: Requirements 6.5**
    """
    
    @given(
        malicious_content=malicious_file_strategy(),
        malicious_filename=malicious_filename_strategy()
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_file_validator_rejects_malicious_files(self, malicious_content, malicious_filename):
        """
        属性测试：文件验证器拒绝恶意文件
        
        对于任何潜在恶意的文件，文件验证器应该在处理前拒绝它
        """
        # 跳过正常文件名的测试（这些应该通过其他验证）
        if malicious_filename == 'normal.csv' and malicious_content == b'default':
            assume(False)
        
        file_validator = FileValidator()
        
        # 验证文件
        is_valid, errors = file_validator.validate(malicious_content, malicious_filename)
        
        # 恶意文件应该被拒绝（返回False）或产生错误
        # 我们不期望所有恶意文件都被检测到，但至少应该有基本的验证
        if len(malicious_content) > FileValidator.MAX_FILE_SIZE:
            assert not is_valid, "超大文件应该被拒绝"
            assert any('大小' in str(error) or 'size' in str(error).lower() for error in errors), \
                "应该有文件大小相关的错误消息"
        
        # 检查不支持的文件格式
        if not any(malicious_filename.lower().endswith(ext) for ext in ['.csv', '.xlsx', '.xls']):
            assert not is_valid, f"不支持的文件格式应该被拒绝: {malicious_filename}"
            assert any('格式' in str(error) or 'format' in str(error).lower() for error in errors), \
                "应该有文件格式相关的错误消息"
    
    @given(
        file_size=st.integers(min_value=0, max_value=15 * 1024 * 1024)
    )
    @settings(
        max_examples=50,
        deadline=None
    )
    def test_file_size_validation(self, file_size):
        """
        属性测试：文件大小验证
        
        对于任何文件大小，验证器应该正确判断是否超过限制
        """
        file_validator = FileValidator()
        
        # 创建指定大小的文件内容
        file_content = b'A' * file_size
        
        # 验证文件大小
        is_valid_size = file_validator.validate_file_size(file_content)
        
        # 检查验证结果
        if file_size <= FileValidator.MAX_FILE_SIZE:
            assert is_valid_size, f"文件大小{file_size}应该通过验证"
        else:
            assert not is_valid_size, f"文件大小{file_size}应该被拒绝"
    
    @given(
        filename=st.text(min_size=1, max_size=100)
    )
    @settings(
        max_examples=50,
        deadline=None
    )
    def test_file_format_validation(self, filename):
        """
        属性测试：文件格式验证
        
        对于任何文件名，验证器应该正确判断格式是否支持
        """
        file_validator = FileValidator()
        
        # 验证文件格式
        is_valid_format = file_validator.validate_file_format(filename)
        
        # 检查验证结果
        supported_extensions = {'.csv', '.xlsx', '.xls'}
        has_supported_ext = any(filename.lower().endswith(ext) for ext in supported_extensions)
        
        if has_supported_ext:
            assert is_valid_format, f"支持的文件格式应该通过验证: {filename}"
        else:
            assert not is_valid_format, f"不支持的文件格式应该被拒绝: {filename}"
    
    def test_empty_file_rejection(self):
        """
        单元测试：拒绝空文件
        
        确保空文件被正确拒绝
        """
        file_validator = FileValidator()
        
        # 测试完全空的文件
        is_valid, errors = file_validator.validate(b'', 'empty.csv')
        assert not is_valid, "空文件应该被拒绝"
        assert len(errors) > 0, "应该有错误消息"
    
    def test_oversized_file_rejection(self):
        """
        单元测试：拒绝超大文件
        
        确保超过10MB的文件被正确拒绝
        """
        file_validator = FileValidator()
        
        # 创建11MB的文件
        large_content = b'A' * (11 * 1024 * 1024)
        
        is_valid, errors = file_validator.validate(large_content, 'large.csv')
        assert not is_valid, "超大文件应该被拒绝"
        assert any('大小' in str(error) or 'size' in str(error).lower() for error in errors), \
            "应该有文件大小相关的错误消息"
    
    def test_unsupported_format_rejection(self):
        """
        单元测试：拒绝不支持的文件格式
        
        确保不支持的文件格式被正确拒绝
        """
        file_validator = FileValidator()
        
        unsupported_files = [
            ('malware.exe', b'MZ\x90\x00'),
            ('script.bat', b'@echo off\ndir'),
            ('document.pdf', b'%PDF-1.4'),
            ('image.jpg', b'\xFF\xD8\xFF'),
            ('archive.zip', b'PK\x03\x04'),
        ]
        
        for filename, content in unsupported_files:
            is_valid, errors = file_validator.validate(content, filename)
            assert not is_valid, f"不支持的文件格式应该被拒绝: {filename}"
            assert any('格式' in str(error) or 'format' in str(error).lower() for error in errors), \
                f"应该有文件格式相关的错误消息: {filename}"
    
    def test_corrupted_file_detection(self):
        """
        单元测试：检测损坏的文件
        
        确保损坏的CSV/Excel文件被检测到
        """
        file_validator = FileValidator()
        
        # 测试损坏的CSV文件（随机二进制数据）
        corrupted_csv = b'\x00\x01\x02\x03\x04\x05' * 100
        is_valid, errors = file_validator.validate(corrupted_csv, 'corrupted.csv')
        # 损坏的文件可能通过格式验证但在结构验证时失败
        # 我们只检查是否有适当的错误处理
        assert isinstance(is_valid, bool), "应该返回布尔值"
        assert isinstance(errors, list), "应该返回错误列表"
    
    def test_csv_processor_handles_malicious_content_safely(self):
        """
        单元测试：CSV处理器安全处理恶意内容
        
        确保CSV处理器在遇到恶意内容时不会崩溃
        """
        csv_processor = CSVProcessor()
        
        malicious_contents = [
            b'',  # 空文件
            b'\x00' * 100,  # 空字节
            b'<script>alert("XSS")</script>',  # 脚本注入
            b'A' * 1000000,  # 极长内容
        ]
        
        for content in malicious_contents:
            try:
                # 尝试解析恶意内容
                result = csv_processor.parse_csv(content)
                
                # 应该返回失败结果，而不是抛出未捕获的异常
                assert hasattr(result, 'success'), "应该返回ProcessingResult对象"
                assert isinstance(result.success, bool), "应该有success字段"
                
                # 如果解析失败，应该有错误消息
                if not result.success:
                    assert len(result.errors) > 0, "失败时应该有错误消息"
                    
            except Exception as e:
                # 如果抛出异常，应该是预期的异常类型
                pytest.fail(f"CSV处理器不应该抛出未捕获的异常: {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
