"""
Flask middleware for automatic input sanitization.

This module provides middleware and decorators for automatic sanitization
of incoming request data.
"""

from typing import Callable, Any, Dict, Optional
from functools import wraps
from flask import request
from mod.sanitizer import InputSanitizer
from mod.logging_config import get_logger

logger = get_logger(__name__)


def sanitize_request_data(f: Callable) -> Callable:
    """
    Decorator to automatically sanitize request data.
    
    Sanitizes JSON body, form data, and query parameters.
    
    Args:
        f: Flask route function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Store sanitized data in request context
        if request.method == 'POST' or request.method == 'PUT' or request.method == 'PATCH':
            if request.is_json:
                try:
                    json_data = request.get_json()
                    if json_data:
                        sanitized_json = InputSanitizer.sanitize_dict(json_data)
                        # Store sanitized data - flask doesn't allow direct modification
                        # but we can set it in g context
                        from flask import g
                        g.sanitized_json = sanitized_json
                except Exception as e:
                    logger.warning(f"Error sanitizing JSON data: {e}")
            
            # Sanitize form data
            if request.form:
                sanitized_form = InputSanitizer.sanitize_dict(request.form.to_dict())
                from flask import g
                g.sanitized_form = sanitized_form
        
        # Sanitize query parameters
        if request.args:
            sanitized_args = InputSanitizer.sanitize_dict(request.args.to_dict())
            from flask import g
            g.sanitized_args = sanitized_args
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_sanitized_json() -> Optional[Dict[str, Any]]:
    """
    Get sanitized JSON data from request.
    
    Returns:
        Sanitized JSON data, or original if not sanitized
    """
    from flask import g, request
    
    if hasattr(g, 'sanitized_json'):
        return g.sanitized_json
    
    if request.is_json:
        return request.get_json()
    
    return None


def get_sanitized_form() -> Optional[Dict[str, Any]]:
    """
    Get sanitized form data from request.
    
    Returns:
        Sanitized form data, or original if not sanitized
    """
    from flask import g, request
    
    if hasattr(g, 'sanitized_form'):
        return g.sanitized_form
    
    if request.form:
        return request.form.to_dict()
    
    return None


def get_sanitized_args() -> Optional[Dict[str, Any]]:
    """
    Get sanitized query parameters from request.
    
    Returns:
        Sanitized arguments, or original if not sanitized
    """
    from flask import g, request
    
    if hasattr(g, 'sanitized_args'):
        return g.sanitized_args
    
    if request.args:
        return request.args.to_dict()
    
    return None


def sanitize_before_response(f: Callable) -> Callable:
    """
    Decorator to sanitize data before sending response.
    
    Ensures sensitive data isn't leaked in responses.
    
    Args:
        f: Flask route function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # If result is a dict, sanitize it
        if isinstance(result, dict):
            result = InputSanitizer.sanitize_dict(result, sanitize_values=False)
        
        return result
    
    return decorated_function


def require_no_xss(parameter_name: str = 'data') -> Callable:
    """
    Decorator to check for XSS attempts in request data.
    
    Args:
        parameter_name: Name of parameter to check
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from mod.exceptions import ValidationError as AppValidationError
            
            # Check JSON data
            if request.is_json:
                json_data = request.get_json()
                if json_data:
                    if isinstance(json_data, str):
                        if InputSanitizer.detect_xss_attempt(json_data):
                            logger.warning("XSS attempt detected in JSON data")
                            raise AppValidationError("Potential XSS attack detected")
                    elif isinstance(json_data, dict):
                        for key, value in json_data.items():
                            if isinstance(value, str):
                                if InputSanitizer.detect_xss_attempt(value):
                                    logger.warning(f"XSS attempt detected in field: {key}")
                                    raise AppValidationError(f"Potential XSS attack detected in {key}")
            
            # Check form data
            if request.form:
                for key, value in request.form.to_dict().items():
                    if InputSanitizer.detect_xss_attempt(value):
                        logger.warning(f"XSS attempt detected in form field: {key}")
                        raise AppValidationError(f"Potential XSS attack detected in {key}")
            
            # Check query parameters
            if request.args:
                for key, value in request.args.to_dict().items():
                    if InputSanitizer.detect_xss_attempt(value):
                        logger.warning(f"XSS attempt detected in query parameter: {key}")
                        raise AppValidationError(f"Potential XSS attack detected in {key}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_no_sql_injection() -> Callable:
    """
    Decorator to check for SQL injection attempts in request data.
    
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from mod.exceptions import ValidationError as AppValidationError
            
            # Check JSON data
            if request.is_json:
                json_data = request.get_json()
                if json_data:
                    if isinstance(json_data, str):
                        if InputSanitizer.detect_sql_injection_attempt(json_data):
                            logger.warning("SQL injection attempt detected in JSON data")
                            raise AppValidationError("Potential SQL injection attack detected")
                    elif isinstance(json_data, dict):
                        for key, value in json_data.items():
                            if isinstance(value, str):
                                if InputSanitizer.detect_sql_injection_attempt(value):
                                    logger.warning(f"SQL injection attempt detected in field: {key}")
                                    raise AppValidationError(f"Potential SQL injection attack detected in {key}")
            
            # Check form data
            if request.form:
                for key, value in request.form.to_dict().items():
                    if InputSanitizer.detect_sql_injection_attempt(value):
                        logger.warning(f"SQL injection attempt detected in form field: {key}")
                        raise AppValidationError(f"Potential SQL injection attack detected in {key}")
            
            # Check query parameters
            if request.args:
                for key, value in request.args.to_dict().items():
                    if InputSanitizer.detect_sql_injection_attempt(value):
                        logger.warning(f"SQL injection attempt detected in query parameter: {key}")
                        raise AppValidationError(f"Potential SQL injection attack detected in {key}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
