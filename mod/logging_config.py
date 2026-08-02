"""Centralized logging configuration for the Growing Grubs application."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from flask import Flask


def setup_logging(app: Optional[Flask] = None) -> logging.Logger:
    """
    Configure logging for the application with both file and console handlers.
    
    Args:
        app: Flask application instance (optional). If provided, also configures the app logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Define log file paths
    log_dir = os.getcwd()
    app_log_file = os.path.join(log_dir, 'app.log')
    error_log_file = os.path.join(log_dir, 'app_errors.log')
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Create formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # File handler for all logs (with rotation)
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for errors only (with rotation)
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Configure Flask app logger if provided
    if app:
        app.logger.setLevel(logging.DEBUG)
        # Remove default Flask handlers
        app.logger.handlers = []
        # Add our handlers to Flask logger
        for handler in root_logger.handlers:
            app.logger.addHandler(handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
