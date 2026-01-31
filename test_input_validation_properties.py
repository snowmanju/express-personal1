"""
Property-based tests for input validation consistency.

Feature: express-tracking-website, Property 2: Input validation consistency
Validates: Requirements 1.5, 6.1

This module tests that for any user input tracking number, if the input is blank,
contains illegal characters, or has invalid format, the system should reject
the query request and return descriptive error messages.
"""

import sys
import os
sys.path.insert(0, '.')

from hypothesis import given, strategies as st, settings, assume
import pytest
import string
import re

from app.services.input_validator import (
    InputValidator, 
    validate_tracking_number, 
    validate_and_clean_input,
    ValidationResult
)


class TestInputValidationConsistency:
    """Test input validation consistency properties."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    @given(st.one_of(
        st.just(""),
        st.text(alphabet=" \t\n\r", min_size=1, max_size=10),
        st.just(None)
    ))
    @settings(max_examples=10, deadline=None)
    def test_blank_input_rejection_property(self, input_text):
        """
        Property: Blank inputs should always be rejected.
        
        For any input that is empty or contains only whitespace,
        the validation should fail and return descriptive error messages.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        # Convert None to empty string for testing
        if input_text is None:
            input_text = ""
        
        result = validate_tracking_number(input_text)
        
        # Property: Blank inputs must be rejected
        assert not result.is_valid, f"Blank input should be rejected: '{input_text}'"
        assert len(result.errors) > 0, "Should provide error messages for blank input"
        
        # Should indicate empty input error or length error (both are valid for blank inputs)
        error_messages = " ".join(result.errors)
        assert any(keyword in error_messages for keyword in [
            "不能为空", "长度不能少于6位"
        ]), f"Should indicate empty or length error for blank input, got: {result.errors}"
    
    @given(st.text(alphabet=string.ascii_letters + string.digits + "!@#$%^&*()[]{}|\\:;\"'<>?,./`~", min_size=6, max_size=30))
    @settings(max_examples=10, deadline=None)
    def test_illegal_characters_rejection_property(self, input_text):
        """
        Property: Inputs with illegal characters should be rejected.
        
        For any input containing characters that are not alphanumeric,
        the validation should fail and return descriptive error messages.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        # Test only inputs that contain illegal characters (non-alphanumeric) and have valid length
        assume(not re.match(r'^[A-Za-z0-9]+$', input_text))
        assume(input_text.strip())  # Not blank
        assume(6 <= len(input_text) <= 30)  # Valid length to test character validation
        
        result = validate_tracking_number(input_text)
        
        # Property: Inputs with illegal characters must be rejected
        assert not result.is_valid, f"Input with illegal characters should be rejected: '{input_text}'"
        assert len(result.errors) > 0, "Should provide error messages for illegal characters"
        
        # Should indicate either character restriction or security issue
        error_messages = " ".join(result.errors)
        assert any(keyword in error_messages for keyword in [
            "只能包含字母和数字", "不安全", "特殊字符", "脚本代码", "SQL代码", "命令注入攻击模式"
        ]), f"Should indicate character or security error, got: {result.errors}"
    
    @given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=5))
    @settings(max_examples=10, deadline=None)
    def test_too_short_format_rejection_property(self, input_text):
        """
        Property: Inputs that are too short should be rejected.
        
        For any alphanumeric input shorter than 6 characters,
        the validation should fail and return descriptive error messages.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        # Test only inputs that are too short (less than 6 characters)
        assume(len(input_text) < 6)
        assume(input_text.strip())  # Not blank
        
        result = validate_tracking_number(input_text)
        
        # Property: Too short inputs must be rejected
        assert not result.is_valid, f"Too short input should be rejected: '{input_text}'"
        assert len(result.errors) > 0, "Should provide error messages for too short input"
        assert any("长度不能少于6位" in error for error in result.errors), \
            f"Should indicate length error, got: {result.errors}"
    
    @given(st.text(alphabet=string.ascii_letters + string.digits, min_size=31, max_size=50))
    @settings(max_examples=10, deadline=None)
    def test_too_long_format_rejection_property(self, input_text):
        """
        Property: Inputs that are too long should be rejected.
        
        For any alphanumeric input longer than 30 characters,
        the validation should fail and return descriptive error messages.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        # Test only inputs that are too long (more than 30 characters)
        assume(len(input_text) > 30)
        
        result = validate_tracking_number(input_text)
        
        # Property: Too long inputs must be rejected
        assert not result.is_valid, f"Too long input should be rejected: '{input_text}'"
        assert len(result.errors) > 0, "Should provide error messages for too long input"
        assert any("长度不能超过30位" in error for error in result.errors), \
            f"Should indicate length error, got: {result.errors}"
    
    @given(st.sampled_from([
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "'; DROP TABLE users; --",
        "UNION SELECT * FROM users",
        "onload=alert(1)",
        "<iframe src='evil.com'></iframe>",
        "SELECT * FROM cargo_manifest",
        "<img src=x onerror=alert(1)>",
        "eval('malicious code')",
        "document.cookie"
    ]))
    @settings(max_examples=10, deadline=None)
    def test_malicious_input_rejection_property(self, malicious_input):
        """
        Property: Malicious inputs should always be rejected.
        
        For any input containing potential security threats (XSS, SQL injection, etc.),
        the validation should fail and return descriptive error messages.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        result = validate_tracking_number(malicious_input)
        
        # Property: Malicious inputs must be rejected
        assert not result.is_valid, f"Malicious input should be rejected: '{malicious_input}'"
        assert len(result.errors) > 0, "Should provide error messages for malicious input"
        
        # Should indicate security issue or format issue (both are valid rejections)
        error_messages = " ".join(result.errors)
        assert any(keyword in error_messages for keyword in [
            "不安全", "脚本代码", "SQL代码", "特殊字符", "只能包含字母和数字", "长度不能少于6位", "长度不能超过30位"
        ]), f"Should indicate security or format error, got: {result.errors}"
    
    @given(st.text(alphabet=string.ascii_letters + string.digits, min_size=6, max_size=30))
    @settings(max_examples=10, deadline=None)
    def test_valid_format_acceptance_property(self, input_text):
        """
        Property: Valid format inputs should be accepted.
        
        For any alphanumeric input between 6-30 characters,
        the validation should succeed and return cleaned value.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        # Test only inputs that should be valid (alphanumeric, proper length)
        assume(6 <= len(input_text) <= 30)
        assume(re.match(r'^[A-Za-z0-9]+$', input_text))
        
        result = validate_tracking_number(input_text)
        
        # Property: Valid format inputs should be accepted
        assert result.is_valid, f"Valid format input should be accepted: '{input_text}', errors: {result.errors}"
        assert result.cleaned_value is not None, "Should provide cleaned value for valid input"
        assert len(result.errors) == 0, f"Should not have errors for valid input, got: {result.errors}"
    
    @given(st.text())
    @settings(max_examples=10, deadline=None)
    def test_error_message_consistency_property(self, input_text):
        """
        Property: Error messages should be consistent and descriptive.
        
        For any invalid input, the validation should always provide
        non-empty, descriptive error messages in Chinese.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        result = validate_tracking_number(input_text)
        
        # If validation fails, must have descriptive error messages
        if not result.is_valid:
            assert len(result.errors) > 0, "Failed validation must provide error messages"
            
            for error in result.errors:
                assert isinstance(error, str), "Error messages must be strings"
                assert len(error.strip()) > 0, "Error messages must not be empty"
                # Check that error messages are in Chinese (contain Chinese characters)
                assert any('\u4e00' <= char <= '\u9fff' for char in error), \
                    f"Error messages should be in Chinese: '{error}'"
    
    @given(st.text())
    @settings(max_examples=10, deadline=None)
    def test_validation_result_structure_property(self, input_text):
        """
        Property: Validation results should have consistent structure.
        
        For any input, the validation should always return a ValidationResult
        with proper structure and consistent field relationships.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        result = validate_tracking_number(input_text)
        
        # Property: Result must be ValidationResult instance
        assert isinstance(result, ValidationResult), "Must return ValidationResult instance"
        
        # Property: Must have is_valid boolean field
        assert isinstance(result.is_valid, bool), "is_valid must be boolean"
        
        # Property: Must have errors list
        assert isinstance(result.errors, list), "errors must be a list"
        
        # Property: Consistency between is_valid and errors
        if result.is_valid:
            assert len(result.errors) == 0, "Valid results should have no errors"
            assert result.cleaned_value is not None, "Valid results should have cleaned value"
        else:
            assert len(result.errors) > 0, "Invalid results should have error messages"
    
    @given(st.text(min_size=1))
    @settings(max_examples=10, deadline=None)
    def test_general_input_validation_consistency_property(self, input_text):
        """
        Property: General input validation should be consistent with tracking number validation.
        
        For any input, the general validation function should apply
        similar security and format checks as tracking number validation.
        
        Feature: express-tracking-website, Property 2: Input validation consistency
        Validates: Requirements 1.5, 6.1
        """
        tracking_result = validate_tracking_number(input_text)
        general_result = validate_and_clean_input(input_text, "test_field")
        
        # Property: Both should reject malicious inputs consistently
        if any(pattern in input_text.lower() for pattern in [
            'script', 'javascript', 'select', 'drop', 'union', 'insert', 'delete'
        ]):
            assert not tracking_result.is_valid or not general_result.is_valid, \
                "At least one validation should reject potentially malicious input"
        
        # Property: Both should handle empty/whitespace consistently
        if not input_text.strip():
            assert not tracking_result.is_valid, "Tracking validation should reject empty input"
            assert not general_result.is_valid, "General validation should reject empty input"


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v"])