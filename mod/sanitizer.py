"""
Input sanitization utilities for security and data integrity.

This module provides functions to sanitize user input, preventing common
web vulnerabilities like XSS (Cross-Site Scripting), SQL injection, and
command injection.
"""

import re
from typing import Optional, List, Dict, Any
from urllib.parse import quote, unquote
import html
from mod.logging_config import get_logger

logger = get_logger(__name__)


class InputSanitizer:
    """Utility class for input sanitization."""
    
    # Patterns for common dangerous content
    DANGEROUS_PATTERNS = {
        'script_tag': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        'event_handler': re.compile(r'on\w+\s*=', re.IGNORECASE),
        'style_tag': re.compile(r'<style[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL),
        'html_tag': re.compile(r'<[^>]+>', re.IGNORECASE),
        'sql_injection': re.compile(r"('|\"|-{2}|;|\/\*|\*\/|xp_|sp_|exec|execute|select|insert|update|delete|drop|create|alter|declare)", re.IGNORECASE),
        'command_injection': re.compile(r'[;&|`$(){}[\]<>\\]'),
        'path_traversal': re.compile(r'(\.\.\/|\.\.\\)'),
    }
    
    # Allow list for HTML tags (for rich text fields, if needed)
    ALLOWED_HTML_TAGS = {
        'b', 'strong', 'i', 'em', 'u', 'br', 'p', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
    }
    
    @staticmethod
    def sanitize_string(
        value: str,
        max_length: Optional[int] = None,
        strip: bool = True,
        lowercase: bool = False
    ) -> str:
        """
        Sanitize a string by removing/escaping dangerous characters.
        
        Args:
            value: String to sanitize
            max_length: Maximum length (truncate if exceeded)
            strip: Whether to strip whitespace
            lowercase: Whether to convert to lowercase
            
        Returns:
            Sanitized string
        """
        if not value:
            return ""
        
        # Strip whitespace if requested
        if strip:
            value = value.strip()
        
        # Convert to lowercase if requested
        if lowercase:
            value = value.lower()
        
        # HTML escape to prevent XSS
        value = html.escape(value)
        
        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def sanitize_html(value: str, allowed_tags: Optional[set] = None) -> str:
        """
        Sanitize HTML content, allowing only safe tags.
        
        Args:
            value: HTML string to sanitize
            allowed_tags: Set of allowed HTML tags (uses ALLOWED_HTML_TAGS if not provided)
            
        Returns:
            Sanitized HTML string
        """
        if not value:
            return ""
        
        if allowed_tags is None:
            allowed_tags = InputSanitizer.ALLOWED_HTML_TAGS
        
        # Remove script tags and event handlers
        value = InputSanitizer.DANGEROUS_PATTERNS['script_tag'].sub('', value)
        value = InputSanitizer.DANGEROUS_PATTERNS['event_handler'].sub('', value)
        value = InputSanitizer.DANGEROUS_PATTERNS['style_tag'].sub('', value)
        
        # Remove disallowed HTML tags
        def remove_disallowed_tags(match):
            tag = match.group(1).lower().split()[0]
            if tag not in allowed_tags:
                return ''
            return match.group(0)
        
        # Pattern to match HTML tags
        tag_pattern = re.compile(r'<(/?)(\w+)[^>]*>', re.IGNORECASE)
        
        def replace_tag(match):
            closing_slash = match.group(1)
            tag_name = match.group(2).lower()
            
            if tag_name not in allowed_tags:
                return ''
            
            # Return safe version of tag
            return f'<{closing_slash}{tag_name}>'
        
        value = tag_pattern.sub(replace_tag, value)
        
        return value
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks.
        
        Args:
            filename: Filename to sanitize
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "file"
        
        # Remove path traversal attempts
        filename = InputSanitizer.DANGEROUS_PATTERNS['path_traversal'].sub('', filename)
        
        # Remove special characters except dots, dashes, underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Remove leading dots (hidden files on Unix)
        filename = filename.lstrip('.')
        
        # Ensure filename doesn't become empty
        if not filename:
            filename = "file"
        
        # Truncate if needed
        if len(filename) > max_length:
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                # Has extension
                ext = name_parts[1]
                name = name_parts[0]
                max_name_len = max_length - len(ext) - 1
                filename = f"{name[:max_name_len]}.{ext}"
            else:
                filename = filename[:max_length]
        
        return filename
    
    @staticmethod
    def sanitize_url(url: str, max_length: int = 2000) -> str:
        """
        Sanitize URL to prevent injection attacks.
        
        Args:
            url: URL to sanitize
            max_length: Maximum URL length
            
        Returns:
            Sanitized URL
        """
        if not url:
            return ""
        
        url = url.strip()
        
        # Ensure URL starts with http:// or https://
        if not url.startswith(('http://', 'https://', '/')):
            url = 'https://' + url
        
        # Remove potentially dangerous characters
        # Allow only safe characters in URL
        safe_chars = re.compile(r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]*$')
        
        if not safe_chars.match(url):
            logger.warning(f"Potentially dangerous URL detected: {url[:50]}")
            # Fall back to making it safe
            url = quote(url, safe=':/?#[]@!$&\'()*+,;=%')
        
        # Truncate if needed
        if len(url) > max_length:
            url = url[:max_length]
        
        return url
    
    @staticmethod
    def sanitize_email(email: str, max_length: int = 254) -> str:
        """
        Sanitize email address.
        
        Args:
            email: Email to sanitize
            max_length: Maximum email length
            
        Returns:
            Sanitized email
        """
        if not email:
            return ""
        
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not email_pattern.match(email):
            logger.warning(f"Invalid email format: {email[:50]}")
            return ""
        
        # Truncate if needed
        if len(email) > max_length:
            email = email[:max_length]
        
        return email
    
    @staticmethod
    def sanitize_search_query(query: str, max_length: int = 100) -> str:
        """
        Sanitize search query to prevent injection attacks.
        
        Args:
            query: Search query to sanitize
            max_length: Maximum query length
            
        Returns:
            Sanitized search query
        """
        if not query:
            return ""
        
        query = query.strip()
        
        # Remove potentially dangerous patterns for SQL/command injection
        dangerous_keywords = ['select', 'insert', 'update', 'delete', 'drop', 'exec', 'execute', '--', '/*', '*/', 'xp_', 'sp_']
        for keyword in dangerous_keywords:
            query = re.sub(f'\\b{keyword}\\b', '', query, flags=re.IGNORECASE)
        
        # Remove special characters except spaces, quotes, and common search operators
        query = re.sub(r'[^\w\s\-"\'*]', '', query)
        
        # Truncate if needed
        if len(query) > max_length:
            query = query[:max_length]
        
        return query
    
    @staticmethod
    def sanitize_json_string(value: str) -> str:
        """
        Sanitize a string for safe JSON encoding.
        
        Args:
            value: String to sanitize
            
        Returns:
            Sanitized string safe for JSON
        """
        if not value:
            return ""
        
        # Escape special JSON characters
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')
        value = value.replace('\b', '\\b')
        value = value.replace('\f', '\\f')
        
        return value
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], sanitize_values: bool = True) -> Dict[str, Any]:
        """
        Sanitize all values in a dictionary.
        
        Args:
            data: Dictionary to sanitize
            sanitize_values: Whether to sanitize string values
            
        Returns:
            Dictionary with sanitized values
        """
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            key = InputSanitizer.sanitize_string(str(key)) if isinstance(key, str) else str(key)
            
            # Sanitize value
            if value is None:
                sanitized[key] = None
            elif isinstance(value, str) and sanitize_values:
                sanitized[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(value, sanitize_values)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputSanitizer.sanitize_string(v) if isinstance(v, str) and sanitize_values else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def detect_xss_attempt(value: str) -> bool:
        """
        Detect potential XSS (Cross-Site Scripting) attack.
        
        Args:
            value: String to check
            
        Returns:
            True if potential XSS detected, False otherwise
        """
        if not value:
            return False
        
        # Check for common XSS patterns
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onload\s*=',
            r'onmouseover\s*=',
            r'<iframe',
            r'<embed',
            r'<object',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt detected: {value[:50]}")
                return True
        
        return False
    
    @staticmethod
    def detect_sql_injection_attempt(value: str) -> bool:
        """
        Detect potential SQL injection attack.
        
        Args:
            value: String to check
            
        Returns:
            True if potential SQL injection detected, False otherwise
        """
        if not value:
            return False
        
        # Check for common SQL injection patterns
        sql_patterns = [
            r"'.*?or.*?'",
            r"'.*?and.*?'",
            r"'.*?--",
            r"'.*?/*.*?\*/",
            r'\bunion\b.*?select',
            r'\bdrop\b.*?table',
            r'\bexec\b.*?\(',
            r'\bexecute\b',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt detected: {value[:50]}")
                return True
        
        return False


# Convenience functions
def sanitize(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize a string value."""
    return InputSanitizer.sanitize_string(value, max_length=max_length)


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename."""
    return InputSanitizer.sanitize_filename(filename)


def sanitize_url(url: str) -> str:
    """Sanitize a URL."""
    return InputSanitizer.sanitize_url(url)


def sanitize_email(email: str) -> str:
    """Sanitize an email address."""
    return InputSanitizer.sanitize_email(email)


def sanitize_search(query: str) -> str:
    """Sanitize a search query."""
    return InputSanitizer.sanitize_search_query(query)


def is_xss_attempt(value: str) -> bool:
    """Check for XSS attempt."""
    return InputSanitizer.detect_xss_attempt(value)


def is_sql_injection_attempt(value: str) -> bool:
    """Check for SQL injection attempt."""
    return InputSanitizer.detect_sql_injection_attempt(value)
