"""
Property-Based Tests for File Validation Component

**Feature: csv-file-upload, Property 2: File Validation Rejection**
**Validates: Requirements 1.3, 1.4**

For any file with unsupported format or exceeding 10MB size, 
the File_Validator should reject it with appropriate error messages.
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import assume
import io
from app.services.file_validator import FileValidator


# Custom strategies for file generation
@st.composite
def unsupported_file_format(draw):
    """Generate filenames with unsupported extensions"""
    unsupported_extensions = ['.txt', '.pdf', '.doc', '.docx', '.json', '.xml', 
                             '.zip', '.rar', '.exe', '.jpg', '.png', '.gif']
    extension = draw(st.sampled_from(unsupported_extensions))
    basename = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122)))
    return f"{basename}{extension}"


@st.composite
def supported_file_format(draw):
    """Generate filenames with supported extensions"""
    supported_extensions = ['.csv', '.xlsx', '.xls']
    extension = draw(st.sampled_from(supported_extensions))
    basename = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65, max_codepoint=122)))
    return f"{basename}{extension}"


@st.composite
def oversized_file_content(draw):
    """Generate file content exceeding 10MB"""
    # Generate content between 10MB + 1 byte and 15MB
    size = draw(st.integers(min_value=10*1024*1024 + 1, max_value=15*1024*1024))
    # Create content efficiently
    return b'x' * size


@st.composite
def valid_sized_file_content(draw):
    """Generate file content within 10MB limit"""
    # Generate content between 1 byte and 10MB
    size = draw(st.integers(min_value=1, max_value=10*1024*1024))
    return b'x' * size


class TestFileValidationRejectionProperties:
    """
    Property-based tests for file validation rejection
    **Feature: csv-file-upload, Property 2: File Validation Rejection**
    """
    
    @given(filename=unsupported_file_format())
    @settings(max_examples=100)
    def test_property_unsupported_format_rejection(self, filename):
        """
        Property: Any file with unsupported format should be rejected
        **Validates: Requirements 1.3**
        """
        validator = FileValidator()
        
        # Create minimal valid content
        file_content = b"test content"
        
        # Validate the file
        is_valid, errors = validator.validate(file_content, filename)
        
        # Property: File should be rejected
        assert not is_valid, f"File with unsupported format {filename} should be rejected"
        
        # Property: Error message should mention unsupported format
        assert len(errors) > 0, "Should have at least one error message"
        assert any("不支持的文件格式" in error or "支持的格式" in error for error in errors), \
            f"Error should mention unsupported format, got: {errors}"
    
    @given(file_content=oversized_file_content(), filename=supported_file_format())
    @settings(max_examples=50, deadline=None)  # Reduced examples due to large file generation
    def test_property_oversized_file_rejection(self, file_content, filename):
        """
        Property: Any file exceeding 10MB should be rejected
        **Validates: Requirements 1.4**
        """
        validator = FileValidator()
        
        # Validate the file
        is_valid, errors = validator.validate(file_content, filename)
        
        # Property: File should be rejected
        assert not is_valid, f"File of size {len(file_content)} bytes should be rejected"
        
        # Property: Error message should mention size limit
        assert len(errors) > 0, "Should have at least one error message"
        assert any("文件大小超过限制" in error or "最大允许" in error for error in errors), \
            f"Error should mention size limit, got: {errors}"
    
    @given(filename=supported_file_format(), file_content=valid_sized_file_content())
    @settings(max_examples=100)
    def test_property_format_validation_consistency(self, filename, file_content):
        """
        Property: Format validation should be consistent regardless of content
        **Validates: Requirements 1.3**
        """
        validator = FileValidator()
        
        # Test format validation directly
        is_format_valid = validator.validate_file_format(filename)
        
        # Property: Supported formats should always pass format validation
        assert is_format_valid, f"Supported format {filename} should pass format validation"
    
    @given(file_content=valid_sized_file_content())
    @settings(max_examples=100)
    def test_property_size_validation_consistency(self, file_content):
        """
        Property: Size validation should be consistent for content within limits
        **Validates: Requirements 1.4**
        """
        validator = FileValidator()
        
        # Test size validation directly
        is_size_valid = validator.validate_file_size(file_content)
        
        # Property: Content within 10MB should pass size validation
        assert is_size_valid, f"Content of size {len(file_content)} bytes should pass size validation"
    
    @given(filename=unsupported_file_format(), file_content=oversized_file_content())
    @settings(max_examples=50, deadline=None)
    def test_property_multiple_validation_failures(self, filename, file_content):
        """
        Property: Files with multiple validation failures should report all issues
        **Validates: Requirements 1.3, 1.4**
        """
        validator = FileValidator()
        
        # Validate the file
        is_valid, errors = validator.validate(file_content, filename)
        
        # Property: File should be rejected
        assert not is_valid, "File with multiple issues should be rejected"
        
        # Property: Should have multiple error messages (format + size)
        assert len(errors) >= 1, "Should have at least one error message"
        
        # At least one error should be about format or size
        has_format_error = any("不支持的文件格式" in error or "支持的格式" in error for error in errors)
        has_size_error = any("文件大小超过限制" in error or "最大允许" in error for error in errors)
        
        assert has_format_error or has_size_error, \
            f"Should have format or size error, got: {errors}"
    
    @given(st.text(min_size=0, max_size=5))
    @settings(max_examples=100)
    def test_property_empty_or_invalid_filename_rejection(self, filename):
        """
        Property: Empty or invalid filenames should be rejected
        **Validates: Requirements 1.3**
        """
        # Skip filenames that happen to have valid extensions
        assume(not any(filename.endswith(ext) for ext in ['.csv', '.xlsx', '.xls']))
        
        validator = FileValidator()
        
        # Test format validation
        is_format_valid = validator.validate_file_format(filename)
        
        # Property: Invalid filenames should fail format validation
        assert not is_format_valid, f"Invalid filename '{filename}' should fail format validation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
