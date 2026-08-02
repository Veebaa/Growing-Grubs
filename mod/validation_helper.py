"""
Validation helper utilities for Pydantic schema validation.

This module provides utilities to validate request data using Pydantic schemas
and convert validation errors to appropriate application exceptions.
"""

from typing import Type, TypeVar, Dict, Any, Tuple, Optional, List
from pydantic import BaseModel, ValidationError
from mod.exceptions import ValidationError as AppValidationError
from mod.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class ValidationHelper:
    """Helper class for Pydantic validation."""
    
    @staticmethod
    def validate_request_data(
        data: Dict[str, Any],
        schema: Type[T]
    ) -> Tuple[bool, Optional[T], Optional[Dict[str, Any]]]:
        """
        Validate request data against a Pydantic schema.
        
        Args:
            data: Dictionary of data to validate
            schema: Pydantic schema class to validate against
            
        Returns:
            Tuple of (is_valid, validated_data, errors)
            - is_valid: Boolean indicating if validation passed
            - validated_data: Validated data as schema instance, or None if invalid
            - errors: Dictionary of validation errors, or None if valid
        """
        try:
            validated = schema(**data)
            return True, validated, None
        except ValidationError as e:
            errors = {}
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                errors[field] = error['msg']
            logger.warning(f"Validation error for {schema.__name__}: {errors}")
            return False, None, errors
    
    @staticmethod
    def validate_or_raise(
        data: Dict[str, Any],
        schema: Type[T],
        context: str = "Request validation failed"
    ) -> T:
        """
        Validate request data and raise AppValidationError if invalid.
        
        Args:
            data: Dictionary of data to validate
            schema: Pydantic schema class to validate against
            context: Context message for error
            
        Returns:
            Validated data as schema instance
            
        Raises:
            AppValidationError: If validation fails
        """
        is_valid, validated, errors = ValidationHelper.validate_request_data(data, schema)
        
        if not is_valid:
            logger.warning(f"{context}: {errors}")
            # Format error message
            error_msgs = [f"{field}: {msg}" for field, msg in errors.items()]
            message = f"{context}. {'; '.join(error_msgs)}"
            raise AppValidationError(
                message=message,
                details={'validation_errors': errors}
            )
        
        return validated
    
    @staticmethod
    def convert_validation_error(error: ValidationError) -> Dict[str, Any]:
        """
        Convert Pydantic ValidationError to a dictionary for response.
        
        Args:
            error: Pydantic ValidationError
            
        Returns:
            Dictionary with formatted validation errors
        """
        errors = {}
        for err in error.errors():
            field = '.'.join(str(loc) for loc in err['loc'])
            msg = err['msg']
            
            if field not in errors:
                errors[field] = []
            errors[field].append(msg)
        
        return errors
    
    @staticmethod
    def format_validation_errors(errors: Dict[str, Any]) -> str:
        """
        Format validation errors as a readable string.
        
        Args:
            errors: Dictionary of validation errors
            
        Returns:
            Formatted error string
        """
        messages = []
        for field, error_list in errors.items():
            if isinstance(error_list, list):
                for error in error_list:
                    messages.append(f"{field}: {error}")
            else:
                messages.append(f"{field}: {error_list}")
        
        return "; ".join(messages)
    
    @staticmethod
    def extract_fields(
        schema: Type[T],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract only fields defined in schema from data dictionary.
        
        Args:
            schema: Pydantic schema class
            data: Dictionary to extract from
            
        Returns:
            Dictionary with only schema-defined fields
        """
        schema_fields = schema.model_fields.keys()
        return {k: v for k, v in data.items() if k in schema_fields}


def validate_schema(
    data: Dict[str, Any],
    schema: Type[T]
) -> T:
    """
    Convenience function to validate data against a schema.
    
    Args:
        data: Dictionary of data to validate
        schema: Pydantic schema class
        
    Returns:
        Validated data as schema instance
        
    Raises:
        AppValidationError: If validation fails
    """
    return ValidationHelper.validate_or_raise(data, schema)


def get_validation_errors(
    data: Dict[str, Any],
    schema: Type[T]
) -> Optional[Dict[str, Any]]:
    """
    Get validation errors without raising an exception.
    
    Args:
        data: Dictionary of data to validate
        schema: Pydantic schema class
        
    Returns:
        Dictionary of errors, or None if valid
    """
    is_valid, _, errors = ValidationHelper.validate_request_data(data, schema)
    return errors if not is_valid else None
