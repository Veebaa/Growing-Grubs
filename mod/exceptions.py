"""
Custom exception classes for Growing Grubs application.

This module defines domain-specific exceptions for better error handling
and more meaningful error responses throughout the application.
"""

from typing import Optional, Dict, Any


class GrowingGrubsException(Exception):
    """Base exception class for all Growing Grubs exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            'error': self.error_code,
            'message': self.message,
            'status_code': self.status_code,
            'details': self.details
        }


class ValidationError(GrowingGrubsException):
    """Raised when user input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: The field that failed validation
        """
        details = kwargs.pop('details', {})
        if field:
            details['field'] = field
        super().__init__(message, status_code=400, details=details, **kwargs)


class AuthenticationError(GrowingGrubsException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        """Initialize authentication error."""
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationError(GrowingGrubsException):
    """Raised when user lacks permission for an action."""
    
    def __init__(self, message: str = "You do not have permission to perform this action", **kwargs):
        """Initialize authorization error."""
        super().__init__(message, status_code=403, **kwargs)


class ResourceNotFoundError(GrowingGrubsException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Optional[Any] = None, **kwargs):
        """
        Initialize resource not found error.
        
        Args:
            resource_type: Type of resource that wasn't found
            resource_id: ID of the resource
        """
        if resource_id:
            message = f"{resource_type} with ID {resource_id} not found"
        else:
            message = f"{resource_type} not found"
        
        details = kwargs.pop('details', {})
        details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(message, status_code=404, details=details, **kwargs)


class ConflictError(GrowingGrubsException):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    
    def __init__(self, message: str, **kwargs):
        """Initialize conflict error."""
        super().__init__(message, status_code=409, **kwargs)


class DatabaseError(GrowingGrubsException):
    """Raised when a database operation fails."""
    
    def __init__(self, message: str = "A database error occurred", operation: Optional[str] = None, **kwargs):
        """
        Initialize database error.
        
        Args:
            message: Error message
            operation: The operation that failed
        """
        details = kwargs.pop('details', {})
        if operation:
            details['operation'] = operation
        super().__init__(message, status_code=500, details=details, **kwargs)


class APIError(GrowingGrubsException):
    """Raised when an external API call fails."""
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: int = 503,
        **kwargs
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            api_name: Name of the external API
            status_code: HTTP status code (default: 503 Service Unavailable)
        """
        details = kwargs.pop('details', {})
        if api_name:
            details['api_name'] = api_name
        super().__init__(message, status_code=status_code, details=details, **kwargs)


class InvalidInputError(ValidationError):
    """Raised when input is invalid or malformed."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        """Initialize invalid input error."""
        super().__init__(message, field=field, **kwargs)


class RateLimitError(GrowingGrubsException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        details = kwargs.pop('details', {})
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, status_code=429, details=details, **kwargs)


class OperationError(GrowingGrubsException):
    """Raised when an operation cannot be completed."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        """
        Initialize operation error.
        
        Args:
            message: Error message
            operation: The operation that failed
        """
        details = kwargs.pop('details', {})
        if operation:
            details['operation'] = operation
        super().__init__(message, status_code=400, details=details, **kwargs)
