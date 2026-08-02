"""
Application configuration and constants for Growing Grubs.

This module contains all configuration constants, validation constraints,
error/success messages, and Flask configuration classes used throughout
the application.
"""

import os
from datetime import datetime
from mod.env_loader import EnvLoader

# ============================================================================
# Profile Image Configuration
# ============================================================================
AVAILABLE_PROFILE_IMAGES = [
    'avo.jpg',
    'cherries.jpg',
    'orange.jpg',
    'strawberry.jpg',
    'watermelon.jpg',
    'default.jpg'
]

PROFILE_IMAGES_DISPLAY = {
    'avo.jpg': 'Avocado',
    'cherries.jpg': 'Cherries',
    'orange.jpg': 'Orange',
    'strawberry.jpg': 'Strawberry',
    'watermelon.jpg': 'Watermelon',
    'default.jpg': 'Default'
}


# ============================================================================
# Meal Planning Configuration
# ============================================================================
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

MEALS_PER_DAY = ['breakfast', 'lunch', 'dinner']


# ============================================================================
# Pagination Configuration
# ============================================================================
RECIPES_PER_PAGE = 15
MIN_SEARCH_LENGTH = 2
MAX_SEARCH_LENGTH = 100


# ============================================================================
# NHS API Configuration
# ============================================================================
NHS_API_PARAMS = {
    "page": 1,
    "category": "A",
    "orderBy": "lastReviewed",
    "startDate": "2020-01-01",
    "endDate": "2021-01-01",
    "order": "newest",
    "synonyms": "true"
}

NHS_ARTICLES_TO_FETCH = 2


# ============================================================================
# Input Validation Configuration
# ============================================================================
VALIDATION_CONSTRAINTS = {
    'username': {
        'min': 4,
        'max': 25,
        'pattern': r'^[a-zA-Z0-9_-]+$'
    },
    'first_name': {
        'min': 1,
        'max': 100,
        'pattern': r'^[a-zA-Z\s\'-]+$'
    },
    'last_name': {
        'min': 1,
        'max': 100,
        'pattern': r'^[a-zA-Z\s\'-]+$'
    },
    'email': {
        'min': 5,
        'max': 100,
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'password': {
        'min': 8,
        'max': 128
    }
}


# ============================================================================
# Portion Size Configuration
# ============================================================================
DEFAULT_PORTION_LIMIT = 5
DEFAULT_PORTION_OFFSET = 0


# ============================================================================
# DateTime Configuration
# ============================================================================
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


# ============================================================================
# Error Messages
# ============================================================================
ERROR_MESSAGES = {
    'invalid_credentials': 'Invalid login credentials.',
    'username_taken': 'Sorry! Username already in use.',
    'email_taken': 'Email already registered.',
    'invalid_email': 'Invalid email format.',
    'invalid_profile_image': 'Invalid profile image selected.',
    'password_mismatch': 'Passwords do not match.',
    'database_error': 'A database error occurred. Please try again.',
    'update_error': 'Error updating profile. Please try again later.',
    'deletion_error': 'An error occurred while deleting your account. Please try again later.',
    'search_too_long': 'Search query too long.',
    'search_too_short': f'Search query must be at least {MIN_SEARCH_LENGTH} characters.',
}


# ============================================================================
# Success Messages
# ============================================================================
SUCCESS_MESSAGES = {
    'registration_success': 'You have been successfully registered.',
    'login_success': 'You have been logged in successfully.',
    'logout_success': 'You have been logged out.',
    'profile_update_success': 'Profile updated successfully!',
    'account_deletion_success': 'Your account has been successfully deleted.',
    'meal_plan_creation_success': 'Meal plan created successfully!',
    'favorite_added': 'Recipe added to favorites!',
    'favorite_removed': 'Recipe removed from favorites!',
}


# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE_SIZE = 10485760  # 10MB
LOG_BACKUP_COUNT = 10
ERROR_LOG_BACKUP_COUNT = 5


# ============================================================================
# Database Configuration
# ============================================================================
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False') == 'True'


# ============================================================================
# Session Configuration
# ============================================================================
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days in seconds


# ============================================================================
# Flask Configuration Classes
# ============================================================================
class Config:
    """
    Base Flask application configuration.
    
    Contains default settings shared across all environments.
    Override in environment-specific subclasses.
    """
    SECRET_KEY = EnvLoader.get_string('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_SECRET_KEY = EnvLoader.get_string('WTF_CSRF_SECRET_KEY', 'csrf-secret-key')
    SESSION_TYPE = SESSION_TYPE
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    DATABASE_URL = EnvLoader.get_string('DATABASE_URL', 'sqlite:///./mod/database.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SESSION_COOKIE_SECURE = EnvLoader.get_bool('SESSION_COOKIE_SECURE', False)
    SESSION_COOKIE_HTTPONLY = EnvLoader.get_bool('SESSION_COOKIE_HTTPONLY', True)
    SESSION_COOKIE_SAMESITE = EnvLoader.get_string('SESSION_COOKIE_SAMESITE', 'Lax')


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    Enables debugging, verbose logging, and SQL query echoing for development.
    """
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    Disables debugging and query echoing for performance and security.
    Requires HTTPS and secure cookies.
    """
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    Uses in-memory SQLite database and disables CSRF protection for testing.
    """
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Select configuration based on environment
config_name = EnvLoader.get_string('FLASK_ENV', 'development')
if config_name == 'production':
    current_config = ProductionConfig
elif config_name == 'testing':
    current_config = TestingConfig
else:
    current_config = DevelopmentConfig
