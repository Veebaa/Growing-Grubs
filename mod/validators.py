"""Input validation utilities for the Growing Grubs application."""

import re
from typing import Optional, List, Tuple, Dict, Any
from mod.config import VALIDATION_CONSTRAINTS, ERROR_MESSAGES


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class Validator:
    """Centralized input validator."""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate username format and length.
        
        Args:
            username: Username to validate
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        constraints = VALIDATION_CONSTRAINTS.get('username', {})
        min_len = constraints.get('min', 4)
        max_len = constraints.get('max', 25)
        pattern = constraints.get('pattern', r'^[a-zA-Z0-9_-]+$')
        
        if not username:
            return False, "Username is required."
        
        if len(username) < min_len or len(username) > max_len:
            return False, f"Username must be between {min_len} and {max_len} characters."
        
        if not re.match(pattern, username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens."
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format and length.
        
        Args:
            email: Email to validate
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        constraints = VALIDATION_CONSTRAINTS.get('email', {})
        min_len = constraints.get('min', 5)
        max_len = constraints.get('max', 100)
        pattern = constraints.get('pattern', r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not email:
            return False, "Email is required."
        
        email = email.strip()
        
        if len(email) < min_len or len(email) > max_len:
            return False, f"Email must be between {min_len} and {max_len} characters."
        
        if not re.match(pattern, email):
            return False, "Invalid email format."
        
        return True, None
    
    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> Tuple[bool, Optional[str]]:
        """
        Validate first/last name format and length.
        
        Args:
            name: Name to validate
            field_name: Field name for error messages
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        key = field_name.lower().replace(' ', '_')
        constraints = VALIDATION_CONSTRAINTS.get(key, {})
        min_len = constraints.get('min', 1)
        max_len = constraints.get('max', 100)
        pattern = constraints.get('pattern', r'^[a-zA-Z\s\'-]+$')
        
        if not name:
            return False, f"{field_name} is required."
        
        name = name.strip()
        
        if len(name) < min_len or len(name) > max_len:
            return False, f"{field_name} must be between {min_len} and {max_len} characters."
        
        if not re.match(pattern, name):
            return False, f"{field_name} can only contain letters, spaces, apostrophes, and hyphens."
        
        return True, None
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            min_length: Minimum password length (default: 8)
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        constraints = VALIDATION_CONSTRAINTS.get('password', {})
        min_len = constraints.get('min', min_length)
        max_len = constraints.get('max', 128)
        
        if not password:
            return False, "Password is required."
        
        if len(password) < min_len:
            return False, f"Password must be at least {min_len} characters long."
        
        if len(password) > max_len:
            return False, f"Password must not exceed {max_len} characters."
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not url:
            return True, None  # URL is optional
        
        url_pattern = r'^https?://[^\s]+$'
        if not re.match(url_pattern, url):
            return False, "Invalid URL format. URLs must start with http:// or https://"
        
        if len(url) > 200:
            return False, "URL is too long (max 200 characters)."
        
        return True, None
    
    @staticmethod
    def validate_search_query(query: str, min_length: int = 2, max_length: int = 100) -> Tuple[bool, Optional[str]]:
        """
        Validate search query.
        
        Args:
            query: Search query to validate
            min_length: Minimum query length
            max_length: Maximum query length
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not query:
            return False, "Search query is required."
        
        query = query.strip()
        
        if len(query) < min_length:
            return False, f"Search query must be at least {min_length} characters."
        
        if len(query) > max_length:
            return False, f"Search query must not exceed {max_length} characters."
        
        # Prevent SQL injection attempts (basic check)
        dangerous_patterns = [r"'--", r"/*", r"*/", r"xp_", r"sp_", r"exec", r"execute"]
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Search query contains invalid characters or patterns."
        
        return True, None
    
    @staticmethod
    def validate_field_length(field_name: str, value: str, min_len: int, max_len: int) -> Tuple[bool, Optional[str]]:
        """
        Generic field length validator.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            min_len: Minimum length
            max_len: Maximum length
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not value:
            return False, f"{field_name} is required."
        
        value = str(value).strip()
        
        if len(value) < min_len or len(value) > max_len:
            return False, f"{field_name} must be between {min_len} and {max_len} characters."
        
        return True, None
    
    @staticmethod
    def validate_choice(value: str, choices: List[str], field_name: str = "Field") -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is in a list of allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed choices
            field_name: Name of the field
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not value:
            return False, f"{field_name} is required."
        
        if value not in choices:
            return False, f"Invalid {field_name}. Must be one of: {', '.join(choices)}"
        
        return True, None
    
    @staticmethod
    def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
        """
        Input sanitization using centralized sanitizer module.
        
        Args:
            value: Value to sanitize
            max_length: Maximum allowed length
        
        Returns:
            str: Sanitized value
        """
        from mod.sanitizer import sanitize
        return sanitize(value, max_length=max_length)


def validate_registration_data(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate complete registration form data.
    
    Args:
        data: Dictionary containing registration fields
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Validate username
    is_valid, error = Validator.validate_username(data.get('username', ''))
    if not is_valid:
        return False, error
    
    # Validate first name
    is_valid, error = Validator.validate_name(data.get('first_name', ''), "First name")
    if not is_valid:
        return False, error
    
    # Validate last name
    is_valid, error = Validator.validate_name(data.get('last_name', ''), "Last name")
    if not is_valid:
        return False, error
    
    # Validate email
    is_valid, error = Validator.validate_email(data.get('email', ''))
    if not is_valid:
        return False, error
    
    # Validate password
    is_valid, error = Validator.validate_password(data.get('password', ''))
    if not is_valid:
        return False, error
    
    # Check password confirmation
    if data.get('password') != data.get('confirm_password'):
        return False, ERROR_MESSAGES.get('password_mismatch', 'Passwords do not match.')
    
    return True, None


def validate_profile_update(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate profile update form data.
    
    Args:
        data: Dictionary containing profile fields
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Validate first name
    is_valid, error = Validator.validate_name(data.get('first_name', ''), "First name")
    if not is_valid:
        return False, error
    
    # Validate last name
    is_valid, error = Validator.validate_name(data.get('last_name', ''), "Last name")
    if not is_valid:
        return False, error
    
    # Validate email
    is_valid, error = Validator.validate_email(data.get('email', ''))
    if not is_valid:
        return False, error
    
    # Validate profile image choice
    from mod.config import AVAILABLE_PROFILE_IMAGES
    is_valid, error = Validator.validate_choice(
        data.get('profile_image', ''),
        AVAILABLE_PROFILE_IMAGES,
        "Profile image"
    )
    if not is_valid:
        return False, error
    
    return True, None
