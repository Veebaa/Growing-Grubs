"""
Flask application factory and database initialization module.

This module contains the create_app factory function that initializes
and configures the Flask application with all necessary extensions.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from mod.logging_config import setup_logging

env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

db = SQLAlchemy()

def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Application factory function for creating and configuring the Flask app.
    
    Creates a Flask application instance with the following setup:
    - Database (SQLAlchemy) configuration
    - Migration support (Alembic)
    - CSRF protection
    - Login manager initialization
    - Centralized logging
    - Custom Jinja2 filters
    
    Args:
        test_config: Optional dictionary of test configuration overrides
        
    Returns:
        Flask: Configured Flask application instance
        
    Raises:
        Various configuration errors if required environment variables are missing
    """
    application = Flask(__name__, static_folder='../static')
    basedir = os.path.abspath(os.path.dirname(__file__))
    migrate = Migrate(application, db)
    csrf = CSRFProtect(application)

    # Default configuration
    application.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default_secret_key'),
        WTF_CSRF_SECRET_KEY=os.environ.get('WTF_CSRF_SECRET_KEY', 'default_csrf_secret_key'),
        SESSION_TYPE='filesystem',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Use DATABASE_URL from Render (PostgreSQL)
    if 'DATABASE_URL' in os.environ:
        application.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    else:
        # Fallback to SQLite for local dev if no DATABASE_URL is provided
        application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')


    # Apply test configuration if provided
    if test_config:
        application.config.from_mapping(test_config)

    # Initialize the SQLAlchemy object with the app
    db.init_app(application)

    from mod.user_manager import init_login_manager
    init_login_manager(application)

    # Register error handlers
    from mod.error_handlers import register_error_handlers
    register_error_handlers(application)
    
    # Set up CSRF protection
    from mod.csrf_protection import setup_csrf_protection
    setup_csrf_protection(application)
    
    # Set up dependency injection
    from mod.container import setup_dependencies
    setup_dependencies(application)
    
    # Register blueprints
    from mod.blueprints import auth_bp, health_bp, debug_bp, recipes_bp, meal_planning_bp
    application.register_blueprint(auth_bp, url_prefix='/auth')
    application.register_blueprint(health_bp, url_prefix='')
    application.register_blueprint(debug_bp, url_prefix='/debug')
    application.register_blueprint(recipes_bp, url_prefix='/recipes')
    application.register_blueprint(meal_planning_bp, url_prefix='/meal_planning')

    # Custom Jinja2 filter
    def yesno(value, yes='Yes', no='No'):
        return yes if value else no

    application.jinja_env.filters['yesno'] = yesno

    # Set up centralized logging
    setup_logging(application)

    application.logger.debug("🟢 Flask application started successfully")

    application.config["DEBUG"] = os.getenv('FLASK_DEBUG', 'False') == 'True'
    application.config["PROPAGATE_EXCEPTIONS"] = True

    # Log database connection (without credentials)
    if 'DATABASE_URL' in os.environ:
        application.logger.debug("🔵 Connected to PostgreSQL database")
    else:
        application.logger.debug("🔵 Connected to SQLite database")

    return application
