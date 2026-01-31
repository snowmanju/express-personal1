"""
Input validation and security filtering service.

This module provides comprehensive input validation and security filtering
to prevent malicious inputs and ensure data integrity.
"""

import re
import html
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    cleaned_value: Optional[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class InputValidator:
    """
    Comprehensive input validation and security filtering service.
    
    Provides validation for tracking numbers, input sanitization,
    and protection against common security vulnerabilities.
    """
    
    # Tracking number patterns for common express companies
    TRACKING_PATTERNS = {
        'general': r'^[A-Za-z0-9]{6,30}$',  # General pattern
        'sf_express': r'^SF\d{12}$',  # SF Express
        'ems': r'^[A-Z]{2}\d{9}[A-Z]{2}$',  # EMS
        'yto': r'^YT\d{13}$',  # YTO Express
        'sto': r'^STO\d{12}$',  # STO Express
        'zto': r'^ZTO\d{12}$',  # ZTO Express
        'yunda': r'^YD\d{13}$',  # Yunda Express
        'jd': r'^JD\d{15}$',  # JD Express
        'postal': r'^\d{13}$',  # China Post
    }
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)',
        r'(\'.*\'|".*")',
        r'(\bxp_cmdshell\b)',
        r'(\bsp_executesql\b)',
    ]
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'onkeydown\s*=',
        r'onkeyup\s*=',
        r'onkeypress\s*=',
        r'onmousedown\s*=',
        r'onmouseup\s*=',
        r'onmousemove\s*=',
        r'onmouseout\s*=',
        r'onmouseenter\s*=',
        r'onmouseleave\s*=',
        r'oncontextmenu\s*=',
        r'ondblclick\s*=',
        r'onwheel\s*=',
        r'onscroll\s*=',
        r'onresize\s*=',
        r'onselect\s*=',
        r'oninput\s*=',
        r'oninvalid\s*=',
        r'onreset\s*=',
        r'onsearch\s*=',
        r'ondrag\s*=',
        r'ondrop\s*=',
        r'ondragover\s*=',
        r'ondragstart\s*=',
        r'ondragend\s*=',
        r'ondragenter\s*=',
        r'ondragleave\s*=',
        r'oncut\s*=',
        r'oncopy\s*=',
        r'onpaste\s*=',
        # CRLF injection patterns
        r'\r\n.*Set-Cookie:',
        r'\n.*Location:',
        r'\r\n.*Location:',
        r'\r\n.*Content-Type:',
        r'\n.*Content-Type:',
        r'\r\n.*Cache-Control:',
        r'\n.*Cache-Control:',
    ]
    
    def __init__(self):
        """Initialize the input validator."""
        self.compiled_sql_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS
        ]
        self.compiled_xss_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.XSS_PATTERNS
        ]
        self.compiled_tracking_patterns = {
            name: re.compile(pattern) for name, pattern in self.TRACKING_PATTERNS.items()
        }
    
    def validate_tracking_number(self, tracking_number: str) -> ValidationResult:
        """
        Validate tracking number format and security.
        
        Args:
            tracking_number: The tracking number to validate
            
        Returns:
            ValidationResult with validation status and cleaned value
        """
        if not tracking_number:
            return ValidationResult(
                is_valid=False,
                errors=["快递单号不能为空"]
            )
        
        # Basic cleaning
        cleaned = self._basic_clean(tracking_number)
        
        # Security validation
        security_result = self._validate_security(cleaned)
        if not security_result.is_valid:
            logger.warning(f"Security validation failed for input: {tracking_number[:10]}...")
            return security_result
        
        # Format validation
        format_result = self._validate_tracking_format(cleaned)
        if not format_result.is_valid:
            return format_result
        
        return ValidationResult(
            is_valid=True,
            cleaned_value=cleaned
        )
    
    def validate_and_clean_input(self, input_value: Any, field_name: str = "input") -> ValidationResult:
        """
        General input validation and cleaning.
        
        Args:
            input_value: The input value to validate and clean
            field_name: Name of the field for error messages
            
        Returns:
            ValidationResult with validation status and cleaned value
        """
        if input_value is None:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}不能为空"]
            )
        
        # Convert to string
        str_value = str(input_value).strip()
        
        if not str_value:
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}不能为空"]
            )
        
        # Basic cleaning
        cleaned = self._basic_clean(str_value)
        
        # Security validation
        security_result = self._validate_security(cleaned)
        if not security_result.is_valid:
            logger.warning(f"Security validation failed for {field_name}: {str_value[:10]}...")
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name}包含不安全的内容"]
            )
        
        return ValidationResult(
            is_valid=True,
            cleaned_value=cleaned
        )
    
    def _basic_clean(self, input_str: str) -> str:
        """
        Perform basic input cleaning.
        
        Args:
            input_str: Input string to clean
            
        Returns:
            Cleaned string
        """
        if not input_str:
            return ""
        
        # Remove leading/trailing whitespace
        cleaned = input_str.strip()
        
        # Remove null bytes
        cleaned = cleaned.replace('\x00', '')
        
        # Remove other control characters except newline and tab
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\t')
        
        # HTML escape to prevent XSS
        cleaned = html.escape(cleaned)
        
        return cleaned
    
    def _validate_security(self, input_str: str) -> ValidationResult:
        """
        Validate input for security vulnerabilities.
        
        Args:
            input_str: Input string to validate
            
        Returns:
            ValidationResult indicating security validation status
        """
        errors = []
        
        # Check for SQL injection patterns
        for pattern in self.compiled_sql_patterns:
            if pattern.search(input_str):
                errors.append("输入包含可疑的SQL代码")
                break
        
        # Check for XSS patterns
        for pattern in self.compiled_xss_patterns:
            if pattern.search(input_str):
                errors.append("输入包含可疑的脚本代码")
                break
        
        # Check for path traversal patterns
        path_traversal_patterns = [
            r'\.\./.*',  # ../
            r'\.\.\\.*',  # ..\
            r'\.\.//.*',  # ..//
            r'\.\.\\\\.*',  # ..\\
            r'\.\.%2f.*',  # ..%2f (URL encoded)
            r'\.\.%5c.*',  # ..%5c (URL encoded)
            r'%2e%2e%2f.*',  # %2e%2e%2f (URL encoded ../)
            r'%2e%2e%5c.*',  # %2e%2e%5c (URL encoded ..\)
        ]
        
        for pattern in path_traversal_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                errors.append("输入包含路径遍历攻击模式")
                break
        
        # Check for command injection patterns
        command_injection_patterns = [
            r';\s*\w+',  # ; command
            r'\|\s*\w+',  # | command
            r'&&\s*\w+',  # && command
            r'\$\(\w+\)',  # $(command)
            r'`\w+`',  # `command`
        ]
        
        for pattern in command_injection_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                errors.append("输入包含命令注入攻击模式")
                break
        
        # Check for excessive length (potential DoS)
        if len(input_str) > 1000:
            errors.append("输入长度超出限制")
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
        if any(char in input_str for char in suspicious_chars):
            # Allow some characters for tracking numbers but be cautious
            if not self._is_tracking_number_context(input_str):
                errors.append("输入包含不允许的特殊字符")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _validate_tracking_format(self, tracking_number: str) -> ValidationResult:
        """
        Validate tracking number format against known patterns.
        
        Args:
            tracking_number: Tracking number to validate
            
        Returns:
            ValidationResult indicating format validation status
        """
        # Remove any remaining HTML entities
        cleaned = html.unescape(tracking_number)
        
        # Check against known patterns
        for pattern_name, pattern in self.compiled_tracking_patterns.items():
            if pattern.match(cleaned):
                return ValidationResult(
                    is_valid=True,
                    cleaned_value=cleaned
                )
        
        # If no specific pattern matches, check general constraints
        if len(cleaned) < 6:
            return ValidationResult(
                is_valid=False,
                errors=["快递单号长度不能少于6位"]
            )
        
        if len(cleaned) > 30:
            return ValidationResult(
                is_valid=False,
                errors=["快递单号长度不能超过30位"]
            )
        
        # Check for valid characters (alphanumeric only)
        if not re.match(r'^[A-Za-z0-9]+$', cleaned):
            return ValidationResult(
                is_valid=False,
                errors=["快递单号只能包含字母和数字"]
            )
        
        return ValidationResult(
            is_valid=True,
            cleaned_value=cleaned
        )
    
    def _is_tracking_number_context(self, input_str: str) -> bool:
        """
        Check if input appears to be in tracking number context.
        
        Args:
            input_str: Input string to check
            
        Returns:
            True if appears to be tracking number context
        """
        # Simple heuristic: mostly alphanumeric with reasonable length
        alphanumeric_ratio = sum(1 for c in input_str if c.isalnum()) / len(input_str) if input_str else 0
        return alphanumeric_ratio > 0.8 and 6 <= len(input_str) <= 30
    
    def validate_file_upload(self, filename: str, file_size: int, allowed_extensions: List[str]) -> ValidationResult:
        """
        Validate file upload parameters.
        
        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            allowed_extensions: List of allowed file extensions
            
        Returns:
            ValidationResult indicating file validation status
        """
        errors = []
        
        if not filename:
            errors.append("文件名不能为空")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Clean filename
        cleaned_filename = self._basic_clean(filename)
        
        # Security validation for filename
        security_result = self._validate_security(cleaned_filename)
        if not security_result.is_valid:
            errors.append("文件名包含不安全的内容")
        
        # Check file extension
        if '.' not in cleaned_filename:
            errors.append("文件必须有扩展名")
        else:
            extension = cleaned_filename.rsplit('.', 1)[1].lower()
            if extension not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"不支持的文件格式，仅支持: {', '.join(allowed_extensions)}")
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            errors.append("文件大小不能超过10MB")
        
        # Check for suspicious filename patterns
        suspicious_patterns = [
            r'\.\./',  # Path traversal
            r'[<>:"|?*]',  # Invalid filename characters
            r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, cleaned_filename, re.IGNORECASE):
                errors.append("文件名包含不允许的字符或模式")
                break
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            cleaned_value=cleaned_filename,
            errors=errors
        )
    
    def sanitize_search_query(self, query: str) -> ValidationResult:
        """
        Sanitize search query input.
        
        Args:
            query: Search query to sanitize
            
        Returns:
            ValidationResult with sanitized query
        """
        if not query:
            return ValidationResult(
                is_valid=False,
                errors=["搜索关键词不能为空"]
            )
        
        # Basic cleaning
        cleaned = self._basic_clean(query)
        
        # Security validation
        security_result = self._validate_security(cleaned)
        if not security_result.is_valid:
            return ValidationResult(
                is_valid=False,
                errors=["搜索关键词包含不安全的内容"]
            )
        
        # Additional sanitization for search
        # Remove SQL wildcards that could be abused
        cleaned = cleaned.replace('%', '').replace('_', '')
        
        # Limit length
        if len(cleaned) > 100:
            cleaned = cleaned[:100]
        
        return ValidationResult(
            is_valid=True,
            cleaned_value=cleaned
        )


# Global validator instance
input_validator = InputValidator()


def validate_tracking_number(tracking_number: str) -> ValidationResult:
    """
    Convenience function to validate tracking number.
    
    Args:
        tracking_number: Tracking number to validate
        
    Returns:
        ValidationResult with validation status
    """
    return input_validator.validate_tracking_number(tracking_number)


def validate_and_clean_input(input_value: Any, field_name: str = "input") -> ValidationResult:
    """
    Convenience function to validate and clean general input.
    
    Args:
        input_value: Input value to validate
        field_name: Field name for error messages
        
    Returns:
        ValidationResult with validation status
    """
    return input_validator.validate_and_clean_input(input_value, field_name)


def sanitize_search_query(query: str) -> ValidationResult:
    """
    Convenience function to sanitize search queries.
    
    Args:
        query: Search query to sanitize
        
    Returns:
        ValidationResult with sanitized query
    """
    return input_validator.sanitize_search_query(query)