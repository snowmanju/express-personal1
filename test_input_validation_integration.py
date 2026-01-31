"""
Integration test for input validation with intelligent query service.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.intelligent_query_service import IntelligentQueryService
from app.services.input_validator import validate_tracking_number


def test_input_validation_integration():
    """Test that input validation integrates properly with the query service."""
    
    # Test valid tracking number
    valid_number = "SF1234567890123"
    result = validate_tracking_number(valid_number)
    assert result.is_valid
    assert result.cleaned_value == valid_number
    
    # Test invalid tracking number
    invalid_number = "<script>alert('xss')</script>"
    result = validate_tracking_number(invalid_number)
    assert not result.is_valid
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_intelligent_query_with_validation():
    """Test intelligent query service with input validation."""
    
    # Mock database session
    mock_db = Mock()
    
    # Create service instance
    service = IntelligentQueryService(mock_db)
    
    # Mock the kuaidi100 client
    service.kuaidi100_client = Mock()
    service.kuaidi100_client.query_tracking = AsyncMock(return_value={
        "success": True,
        "company_code": "SF",
        "company_name": "顺丰速运",
        "status": "在途中",
        "tracks": [
            {
                "time": "2024-01-01 10:00:00",
                "location": "深圳市",
                "description": "快件已发出"
            }
        ],
        "query_time": "2024-01-01T10:00:00Z"
    })
    
    # Mock the manifest lookup
    service._find_manifest_by_tracking_number = AsyncMock(return_value=None)
    
    # Test with valid tracking number
    result = await service.query_tracking("SF1234567890123")
    assert result["success"] == True
    assert "cleaned_tracking_number" in result
    assert result["original_tracking_number"] == "SF1234567890123"
    
    # Test with invalid tracking number
    result = await service.query_tracking("<script>alert('xss')</script>")
    assert result["success"] == False
    assert "输入验证失败" in result["error"]


def test_security_patterns():
    """Test that security patterns are properly detected."""
    
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "<script>alert(1)</script>",
        "javascript:alert(1)",
        "onload=alert(1)",
        "<iframe src='evil.com'></iframe>",
        "UNION SELECT * FROM users"
    ]
    
    for malicious_input in malicious_inputs:
        result = validate_tracking_number(malicious_input)
        assert not result.is_valid, f"Should reject malicious input: {malicious_input}"
        assert len(result.errors) > 0


def test_tracking_number_patterns():
    """Test various tracking number patterns."""
    
    valid_patterns = [
        "SF1234567890123",  # SF Express
        "YT1234567890123",  # YTO Express  
        "1234567890123",    # China Post
        "ABC123456789",     # General pattern
        "TEST123456"        # Alphanumeric
    ]
    
    for pattern in valid_patterns:
        result = validate_tracking_number(pattern)
        assert result.is_valid, f"Should accept valid pattern: {pattern}"
    
    invalid_patterns = [
        "",                 # Empty
        "12345",           # Too short
        "A" * 31,          # Too long
        "ABC-123",         # Invalid characters
        "ABC 123",         # Spaces
        "ABC@123"          # Special characters
    ]
    
    for pattern in invalid_patterns:
        result = validate_tracking_number(pattern)
        assert not result.is_valid, f"Should reject invalid pattern: {pattern}"


if __name__ == "__main__":
    # Run synchronous tests
    test_input_validation_integration()
    test_security_patterns()
    test_tracking_number_patterns()
    
    # Run async test
    asyncio.run(test_intelligent_query_with_validation())
    
    print("All integration tests passed!")