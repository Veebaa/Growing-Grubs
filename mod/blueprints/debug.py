"""
Debug and diagnostics routes.

This module contains debug-only routes for development and troubleshooting.
Should be disabled in production.
"""

from flask import Blueprint, current_app, render_template_string
from mod.logging_config import get_logger

logger = get_logger(__name__)

# Create debug blueprint
debug_bp = Blueprint('debug', __name__)


@debug_bp.route("/debug")
def debug():
    """
    Debug route for testing Flask app configuration.
    
    Returns:
        Debug information
    """
    logger.debug("Debug route accessed")
    print("🟢 Debug Route Hit!", flush=True)
    return "Debug route working!", 200


@debug_bp.route('/debug_db')
def debug_db():
    """
    Debug database connection.
    
    Returns:
        Database status information
    """
    from mod import db
    
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        logger.info("Database connection successful")
        return "Database OK!", 200
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return f"Database Error: {e}", 500


@debug_bp.route('/show_log')
def show_log():
    """
    Display application logs (development only).
    
    Returns:
        Log file contents
    """
    try:
        from mod.env_loader import EnvLoader
        log_file = EnvLoader.get_string('LOG_FILE', 'logs/app.log')
        
        with open(log_file, 'r') as f:
            logs = f.read()
        
        return render_template_string(
            '<pre>{{ logs }}</pre>',
            logs=logs
        ), 200
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return f"Error reading logs: {e}", 500
