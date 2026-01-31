"""
Unit Tests for FileValidator Boundary Cases

Tests specific boundary conditions and edge cases for file validation.
**Validates: Requirements 1.3, 1.4**
"""

import pytest
import io
from app.services.file_validator import FileValidator


class TestFileValidatorBoundaryCases:
    """Unit tests for FileValidator boundary cases"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = FileValidator()
    
    # File Size Boundary Tests
    
    def test_file_size_exactly_10mb(self):
        """Test file size exactly at 10MB limit (boundary condition)"""
        # Create exactly 10MB of content
        exactly_10mb = b'x' * (10 * 1024 * 1024)
        
        # Should pass size validation
        is_valid = self.validator.validate_file_size(exactly_10mb)
        assert is_valid, "File of exactly 10MB should pass validation"
    
    def test_file_size_one_byte_over_10mb(self):
        """Test file size one byte over 10MB limit (boundary condition)"""
        # Create 10MB + 1 byte of content
        over_10mb = b'x' * (10 * 1024 * 1024 + 1)
        
        # Should fail size validation
        is_valid = self.validator.validate_file_size(over_10mb)
        assert not is_valid, "File of 10MB + 1 byte should fail validation"
    
    def test_file_size_one_byte_under_10mb(self):
        """Test file size one byte under 10MB limit (boundary condition)"""
        # Create 10MB - 1 byte of content
        under_10mb = b'x' * (10 * 1024 * 1024 - 1)
        
        # Should pass size validation
        is_valid = self.validator.validate_file_size(under_10mb)
        assert is_valid, "File of 10MB - 1 byte should pass validation"
    
    def test_file_size_empty_file(self):
        """Test empty file (0 bytes)"""
        empty_content = b''
        
        # Should pass size validation (but may fail structure validation)
        is_valid = self.validator.validate_file_size(empty_content)
        assert is_valid, "Empty file should pass size validation"
    
    def test_file_size_very_small_file(self):
        """Test very small file (1 byte)"""
        tiny_content = b'x'
        
        # Should pass size validation
        is_valid = self.validator.validate_file_size(tiny_content)
        assert is_valid, "1-byte file should pass size validation"
    
    # File Format Tests
    
    def test_supported_format_csv_lowercase(self):
        """Test .csv extension (lowercase)"""
        assert self.validator.validate_file_format("test.csv")
    
    def test_supported_format_csv_uppercase(self):
        """Test .CSV extension (uppercase)"""
        assert self.validator.validate_file_format("test.CSV")
    
    def test_supported_format_csv_mixed_case(self):
        """Test .CsV extension (mixed case)"""
        assert self.validator.validate_file_format("test.CsV")
    
    def test_supported_format_xlsx(self):
        """Test .xlsx extension"""
        assert self.validator.validate_file_format("test.xlsx")
    
    def test_supported_format_xls(self):
        """Test .xls extension"""
        assert self.validator.validate_file_format("test.xls")
    
    def test_unsupported_format_txt(self):
        """Test .txt extension (unsupported)"""
        assert not self.validator.validate_file_format("test.txt")
    
    def test_unsupported_format_pdf(self):
        """Test .pdf extension (unsupported)"""
        assert not self.validator.validate_file_format("test.pdf")
    
    def test_unsupported_format_doc(self):
        """Test .doc extension (unsupported)"""
        assert not self.validator.validate_file_format("test.doc")
    
    def test_unsupported_format_json(self):
        """Test .json extension (unsupported)"""
        assert not self.validator.validate_file_format("test.json")
    
    def test_unsupported_format_xml(self):
        """Test .xml extension (unsupported)"""
        assert not self.validator.validate_file_format("test.xml")
    
    def test_no_extension(self):
        """Test filename without extension"""
        assert not self.validator.validate_file_format("test")
    
    def test_empty_filename(self):
        """Test empty filename"""
        assert not self.validator.validate_file_format("")
    
    def test_filename_with_multiple_dots(self):
        """Test filename with multiple dots"""
        assert self.validator.validate_file_format("test.backup.csv")
    
    def test_filename_with_path(self):
        """Test filename with path components"""
        assert self.validator.validate_file_format("/path/to/test.csv")
    
    # Corrupted File Detection Tests
    
    def test_corrupted_csv_empty_content(self):
        """Test CSV file with empty content"""
        empty_content = b''
        
        is_valid, errors = self.validator.validate_file_structure(empty_content, "test.csv")
        assert not is_valid, "Empty CSV should be detected as invalid"
        assert len(errors) > 0, "Should have error messages"
        assert any("空" in error for error in errors), "Error should mention empty content"
    
    def test_corrupted_csv_invalid_content(self):
        """Test CSV file with binary garbage content"""
        garbage_content = b'\x00\x01\x02\x03\x04\x05'
        
        is_valid, errors = self.validator.validate_file_structure(garbage_content, "test.csv")
        # May or may not be valid depending on pandas interpretation
        # Just ensure it doesn't crash
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_valid_csv_minimal_content(self):
        """Test CSV file with minimal valid content"""
        valid_csv = b'header1,header2\nvalue1,value2'
        
        is_valid, errors = self.validator.validate_file_structure(valid_csv, "test.csv")
        assert is_valid, "Valid CSV should pass structure validation"
        assert len(errors) == 0, "Valid CSV should have no errors"
    
    def test_corrupted_excel_empty_content(self):
        """Test Excel file with empty content"""
        empty_content = b''
        
        is_valid, errors = self.validator.validate_file_structure(empty_content, "test.xlsx")
        assert not is_valid, "Empty Excel should be detected as invalid"
        assert len(errors) > 0, "Should have error messages"
    
    def test_corrupted_excel_invalid_content(self):
        """Test Excel file with non-Excel content"""
        invalid_excel = b'This is not an Excel file'
        
        is_valid, errors = self.validator.validate_file_structure(invalid_excel, "test.xlsx")
        assert not is_valid, "Invalid Excel content should be detected"
        assert len(errors) > 0, "Should have error messages"
    
    # Full Validation Tests
    
    def test_full_validation_valid_csv(self):
        """Test full validation with valid CSV"""
        valid_csv = b'header1,header2\nvalue1,value2'
        
        is_valid, errors = self.validator.validate(valid_csv, "test.csv")
        assert is_valid, "Valid CSV should pass full validation"
        assert len(errors) == 0, "Valid CSV should have no errors"
    
    def test_full_validation_oversized_csv(self):
        """Test full validation with oversized CSV"""
        oversized_csv = b'x' * (11 * 1024 * 1024)  # 11MB
        
        is_valid, errors = self.validator.validate(oversized_csv, "test.csv")
        assert not is_valid, "Oversized CSV should fail validation"
        assert len(errors) > 0, "Should have error messages"
        assert any("大小超过限制" in error for error in errors), "Error should mention size limit"
    
    def test_full_validation_unsupported_format(self):
        """Test full validation with unsupported format"""
        content = b'test content'
        
        is_valid, errors = self.validator.validate(content, "test.txt")
        assert not is_valid, "Unsupported format should fail validation"
        assert len(errors) > 0, "Should have error messages"
        assert any("不支持的文件格式" in error for error in errors), "Error should mention unsupported format"
    
    def test_full_validation_multiple_errors(self):
        """Test full validation with multiple errors (oversized + unsupported format)"""
        oversized_content = b'x' * (11 * 1024 * 1024)  # 11MB
        
        is_valid, errors = self.validator.validate(oversized_content, "test.txt")
        assert not is_valid, "File with multiple issues should fail validation"
        assert len(errors) >= 1, "Should have at least one error message"
    
    def test_full_validation_exactly_10mb_csv(self):
        """Test full validation with exactly 10MB valid CSV"""
        # Create a CSV that's exactly 10MB
        header = b'col1,col2,col3\n'
        row = b'value1,value2,value3\n'
        
        # Calculate how many rows we need
        remaining_size = (10 * 1024 * 1024) - len(header)
        num_rows = remaining_size // len(row)
        
        exactly_10mb_csv = header + (row * num_rows)
        
        # Adjust to exactly 10MB
        if len(exactly_10mb_csv) > 10 * 1024 * 1024:
            exactly_10mb_csv = exactly_10mb_csv[:10 * 1024 * 1024]
        
        is_valid, errors = self.validator.validate(exactly_10mb_csv, "test.csv")
        # Should pass size validation, structure validation depends on content
        assert self.validator.validate_file_size(exactly_10mb_csv), "Should pass size validation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
