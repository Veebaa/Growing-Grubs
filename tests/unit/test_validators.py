"""
Unit tests for validation utilities.
"""

import pytest
from mod.validators import Validator
from mod.sanitizer import InputSanitizer


@pytest.mark.unit
class TestValidator:
    """Test cases for Validator class."""
    
    def test_validate_username_valid(self):
        """Test valid username validation."""
        is_valid, error = Validator.validate_username('testuser')
        assert is_valid is True
        assert error is None
    
    def test_validate_username_too_short(self):
        """Test username that's too short."""
        is_valid, error = Validator.validate_username('abc')
        assert is_valid is False
        assert error is not None
    
    def test_validate_username_invalid_chars(self):
        """Test username with invalid characters."""
        is_valid, error = Validator.validate_username('test@user!')
        assert is_valid is False
        assert error is not None
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        is_valid, error = Validator.validate_email('test@example.com')
        assert is_valid is True
        assert error is None
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        is_valid, error = Validator.validate_email('notanemail')
        assert is_valid is False
        assert error is not None
    
    def test_validate_password_valid(self):
        """Test valid password validation."""
        is_valid, error = Validator.validate_password('securepass123')
        assert is_valid is True
        assert error is None
    
    def test_validate_password_too_short(self):
        """Test password that's too short."""
        is_valid, error = Validator.validate_password('short')
        assert is_valid is False
        assert error is not None
    
    def test_validate_search_query_valid(self):
        """Test valid search query."""
        is_valid, error = Validator.validate_search_query('healthy recipes')
        assert is_valid is True
        assert error is None
    
    def test_validate_search_query_too_short(self):
        """Test search query that's too short."""
        is_valid, error = Validator.validate_search_query('a')
        assert is_valid is False
        assert error is not None
    
    def test_validate_search_query_sql_injection_attempt(self):
        """Test search query with SQL injection attempt."""
        is_valid, error = Validator.validate_search_query("'; DROP TABLE users; --")
        assert is_valid is False
        assert error is not None
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        result = Validator.sanitize_input('  test input  ')
        assert result == 'test input'
    
    def test_sanitize_input_with_max_length(self):
        """Test input sanitization with max length."""
        result = Validator.sanitize_input('very long string', max_length=5)
        assert len(result) <= 5


@pytest.mark.unit
class TestInputSanitizer:
    """Test cases for InputSanitizer class."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = InputSanitizer.sanitize_string('  test  ')
        assert result == 'test'
    
    def test_sanitize_string_html_escape(self):
        """Test HTML escaping."""
        result = InputSanitizer.sanitize_string('<script>alert("xss")</script>')
        assert '<script>' not in result
        assert 'alert' in result
    
    def test_detect_xss_attempt(self):
        """Test XSS attack detection."""
        xss_payload = '<script>alert("xss")</script>'
        assert InputSanitizer.detect_xss_attempt(xss_payload) is True
    
    def test_detect_xss_attempt_false(self):
        """Test normal input doesn't trigger XSS detection."""
        normal_text = 'This is normal text'
        assert InputSanitizer.detect_xss_attempt(normal_text) is False
    
    def test_detect_sql_injection_attempt(self):
        """Test SQL injection detection."""
        sql_payload = "'; DROP TABLE users; --"
        assert InputSanitizer.detect_sql_injection_attempt(sql_payload) is True
    
    def test_detect_sql_injection_attempt_false(self):
        """Test normal input doesn't trigger SQL injection detection."""
        normal_text = 'This is normal text'
        assert InputSanitizer.detect_sql_injection_attempt(normal_text) is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        result = InputSanitizer.sanitize_filename('my-file_name.txt')
        assert result == 'my-file_name.txt'
    
    def test_sanitize_filename_removes_path_traversal(self):
        """Test that path traversal is removed."""
        result = InputSanitizer.sanitize_filename('../../../etc/passwd')
        assert '..' not in result
    
    def test_sanitize_email(self):
        """Test email sanitization."""
        result = InputSanitizer.sanitize_email('TEST@EXAMPLE.COM')
        assert result == 'test@example.com'
    
    def test_sanitize_email_invalid(self):
        """Test invalid email returns empty string."""
        result = InputSanitizer.sanitize_email('not-an-email')
        assert result == ''
