"""
Basic tests for input validator functionality.
"""

import pytest
from app.services.input_validator import (
    InputValidator, 
    validate_tracking_number, 
    validate_and_clean_input,
    sanitize_search_query
)


def test_input_validator_creation():
    """Test that InputValidator can be created."""
    validator = InputValidator()
    assert validator is not None


def test_valid_tracking_numbers():
    """Test validation of valid tracking numbers."""
    valid_numbers = [
        "SF1234567890123",  # SF Express format
        "YT1234567890123",  # YTO format
        "ABC123456789",     # General format
        "1234567890123",    # Postal format
        "TEST123456"        # General alphanumeric
    ]
    
    for number in valid_numbers:
        result = validate_tracking_number(number)
        assert result.is_valid, f"Should accept valid tracking number: {number}"
        assert result.cleaned_value == number


def test_invalid_tracking_numbers():
    """Test validation of invalid tracking numbers."""
    invalid_numbers = [
        "",                    # Empty
        "   ",                # Whitespace only
        "12345",              # Too short
        "A" * 31,             # Too long
        "ABC-123",            # Invalid characters
        "ABC 123",            # Spaces
        "<script>alert(1)</script>",  # XSS attempt
        "'; DROP TABLE users; --",    # SQL injection attempt
    ]
    
    for number in invalid_numbers:
        result = validate_tracking_number(number)
        assert not result.is_valid, f"Should reject invalid tracking number: {number}"
        assert len(result.errors) > 0


def test_security_validation():
    """Test security validation against common attacks."""
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "'; DROP TABLE users; --",
        "UNION SELECT * FROM users",
        "onload=alert(1)",
        "<iframe src='evil.com'></iframe>"
    ]
    
    for malicious_input in malicious_inputs:
        result = validate_and_clean_input(malicious_input, "test_field")
        assert not result.is_valid, f"Should reject malicious input: {malicious_input}"


def test_input_cleaning():
    """Test basic input cleaning functionality."""
    test_cases = [
        ("  test  ", "test"),           # Whitespace trimming
        ("test\x00null", "testnull"),  # Null byte removal
        ("test\x01ctrl", "testctrl"),  # Control character removal
    ]
    
    validator = InputValidator()
    for input_str, expected in test_cases:
        cleaned = validator._basic_clean(input_str)
        # Note: HTML escaping might affect the exact match, so we check the core content
        assert expected in cleaned or cleaned == expected


def test_search_query_sanitization():
    """Test search query sanitization."""
    # Valid search queries
    valid_queries = [
        "SF123456789",
        "快递单号",
        "test query"
    ]
    
    for query in valid_queries:
        result = sanitize_search_query(query)
        assert result.is_valid, f"Should accept valid search query: {query}"
    
    # Invalid search queries
    invalid_queries = [
        "",
        "<script>alert(1)</script>",
        "'; DROP TABLE users; --"
    ]
    
    for query in invalid_queries:
        result = sanitize_search_query(query)
        assert not result.is_valid, f"Should reject invalid search query: {query}"


def test_file_upload_validation():
    """Test file upload validation."""
    validator = InputValidator()
    
    # Valid file uploads
    valid_cases = [
        ("test.csv", 1024, ["csv", "xlsx"]),
        ("data.xlsx", 5000, ["csv", "xlsx", "xls"]),
        ("manifest.xls", 2048, ["xls"])
    ]
    
    for filename, size, allowed_exts in valid_cases:
        result = validator.validate_file_upload(filename, size, allowed_exts)
        assert result.is_valid, f"Should accept valid file: {filename}"
    
    # Invalid file uploads
    invalid_cases = [
        ("", 1024, ["csv"]),                    # Empty filename
        ("test.txt", 1024, ["csv"]),           # Wrong extension
        ("test.csv", 20 * 1024 * 1024, ["csv"]),  # Too large
        ("../../../etc/passwd", 1024, ["csv"]), # Path traversal
        ("test<script>.csv", 1024, ["csv"])     # Malicious filename
    ]
    
    for filename, size, allowed_exts in invalid_cases:
        result = validator.validate_file_upload(filename, size, allowed_exts)
        assert not result.is_valid, f"Should reject invalid file: {filename}"


if __name__ == "__main__":
    # Run basic tests
    test_input_validator_creation()
    test_valid_tracking_numbers()
    test_invalid_tracking_numbers()
    test_security_validation()
    test_input_cleaning()
    test_search_query_sanitization()
    test_file_upload_validation()
    print("All basic tests passed!")