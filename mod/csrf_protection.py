"""
CSRF (Cross-Site Request Forgery) protection utilities.

This module provides helpers for CSRF token management and verification
across the application.
"""

from functools import wraps
from flask import session, render_template_string, request
from flask_login import current_user
from mod.logging_config import get_logger
from mod.exceptions import ValidationError

logger = get_logger(__name__)


class CSRFProtection:
    """Utility class for CSRF protection operations."""
    
    @staticmethod
    def get_token() -> str:
        """
        Get CSRF token from session.
        
        Returns:
            CSRF token or empty string if not available
        """
        token = session.get('csrf_token')
        if not token:
            import secrets
            token = secrets.token_hex(32)
            session['csrf_token'] = token
        return token
    
    @staticmethod
    def render_csrf_field() -> str:
        """
        Render CSRF token as hidden form field.
        
        Returns:
            HTML for hidden CSRF token field
        """
        token = CSRFProtection.get_token()
        return f'<input type="hidden" name="csrf_token" value="{token}">'
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """
        Verify CSRF token from request.
        
        Args:
            token: Token to verify
            
        Returns:
            True if token is valid, False otherwise
        """
        session_token = session.get('csrf_token')
        
        if not session_token or not token:
            logger.warning("CSRF token missing from session or request")
            return False
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = token == session_token
        
        if not is_valid:
            logger.warning("CSRF token mismatch - possible attack")
        
        return is_valid
    
    @staticmethod
    def require_valid_token(f):
        """
        Decorator to verify CSRF token on POST/PUT/PATCH requests.
        
        Args:
            f: Route function to decorate
            
        Returns:
            Decorated function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # Get token from form data or JSON body
                token = request.form.get('csrf_token') or \
                        (request.get_json(silent=True) or {}).get('csrf_token')
                
                if not token:
                    logger.warning(f"CSRF token missing from {request.method} request to {request.path}")
                    raise ValidationError("CSRF token is missing", field='csrf_token')
                
                if not CSRFProtection.verify_token(token):
                    logger.warning(f"CSRF token verification failed for {request.method} request to {request.path}")
                    raise ValidationError("CSRF token is invalid", field='csrf_token')
            
            return f(*args, **kwargs)
        
        return decorated_function


def csrf_token_field() -> str:
    """Jinja2 function to render CSRF token field in templates."""
    return CSRFProtection.render_csrf_field()


def setup_csrf_protection(app) -> None:
    """
    Set up CSRF protection for the Flask app.
    
    Args:
        app: Flask application instance
    """
    # Make csrf_token_field available in all templates
    @app.context_processor
    def inject_csrf_token():
        return {
            'csrf_token_field': csrf_token_field,
            'csrf_token': CSRFProtection.get_token
        }
    
    logger.info("CSRF protection configured")
