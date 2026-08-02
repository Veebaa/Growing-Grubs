"""
Environment variable loader and validator.

This module handles loading and validating environment variables from .env files
and environment, providing type-safe access to configuration values.
"""

import os
from typing import Optional, Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv

from mod.logging_config import get_logger

logger = get_logger(__name__)


class EnvLoader:
    """Utility for loading and accessing environment variables."""
    
    # Required environment variables that must be set
    REQUIRED_VARS: List[str] = [
        'SECRET_KEY',
        'WTF_CSRF_SECRET_KEY',
    ]
    
    # Optional environment variables with defaults
    OPTIONAL_VARS: Dict[str, Any] = {
        'FLASK_ENV': 'development',
        'DEBUG': 'False',
        'DATABASE_URL': 'sqlite:///./mod/database.db',
        'SQLALCHEMY_ECHO': 'False',
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'logs/app.log',
        'ERROR_LOG_FILE': 'logs/error.log',
        'SESSION_TYPE': 'filesystem',
        'PERMANENT_SESSION_LIFETIME': '604800',
        'SESSION_COOKIE_SECURE': 'False',
        'SESSION_COOKIE_HTTPONLY': 'True',
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'ENABLE_DEBUG_ROUTES': 'True',
        'API_RATE_LIMIT': '1.0',
        'API_MAX_RETRIES': '3',
        'API_REQUEST_TIMEOUT': '10',
    }
    
    @staticmethod
    def load_env_file(env_file: Optional[str] = None) -> None:
        """
        Load environment variables from .env file.
        
        Args:
            env_file: Path to .env file. If None, searches in current directory.
        """
        if env_file:
            env_path = Path(env_file)
        else:
            # Look for .env in current directory and parent directories
            env_path = Path('.env')
            if not env_path.exists():
                env_path = Path(__file__).parent.parent / '.env'
        
        if env_path.exists():
            logger.info(f"Loading environment variables from {env_path}")
            load_dotenv(env_path)
        else:
            logger.warning(f"No .env file found at {env_path}")
    
    @staticmethod
    def get_string(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a string environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Environment variable value or default
        """
        value = os.getenv(key, default)
        if value is None and key in EnvLoader.REQUIRED_VARS:
            logger.error(f"Required environment variable {key} is not set")
        return value
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """
        Get a boolean environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Boolean value
        """
        value = os.getenv(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """
        Get an integer environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Integer value
        """
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default {default}")
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """
        Get a float environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
            
        Returns:
            Float value
        """
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float value for {key}, using default {default}")
            return default
    
    @staticmethod
    def validate_required() -> bool:
        """
        Validate that all required environment variables are set.
        
        Returns:
            True if all required variables are set, False otherwise
        """
        missing = []
        for var in EnvLoader.REQUIRED_VARS:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            return False
        
        logger.info("All required environment variables are set")
        return True
    
    @staticmethod
    def ensure_env_file_exists() -> None:
        """
        Ensure .env file exists, create from .env.example if it doesn't.
        
        This helps with initial setup in development environments.
        """
        env_path = Path('.env')
        example_path = Path('.env.example')
        
        if not env_path.exists() and example_path.exists():
            logger.warning(".env file not found, copying from .env.example")
            try:
                env_path.write_text(example_path.read_text())
                logger.info(".env file created from .env.example template")
            except Exception as e:
                logger.error(f"Failed to create .env from .env.example: {e}")
    
    @staticmethod
    def print_config_summary() -> None:
        """Print a summary of current configuration (without sensitive values)."""
        logger.info("=== Current Configuration ===")
        logger.info(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'development')}")
        logger.info(f"DEBUG: {os.getenv('DEBUG', 'False')}")
        logger.info(f"DATABASE_URL: {EnvLoader._mask_sensitive(os.getenv('DATABASE_URL', 'sqlite:///./mod/database.db'))}")
        logger.info(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
        logger.info(f"ENABLE_DEBUG_ROUTES: {os.getenv('ENABLE_DEBUG_ROUTES', 'True')}")
    
    @staticmethod
    def _mask_sensitive(value: str) -> str:
        """Mask sensitive values in log output."""
        if not value:
            return value
        
        # Mask database passwords
        if '@' in value and ('postgresql' in value or 'mysql' in value):
            parts = value.split('@')
            return f"{parts[0].split('//')[0]}//**MASKED**@{parts[1]}"
        
        return value
