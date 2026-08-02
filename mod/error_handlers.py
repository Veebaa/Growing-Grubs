"""
Flask error handlers for consistent error responses.

This module registers global error handlers for various exception types
and HTTP error codes to provide consistent JSON error responses and
user-friendly error pages.
"""

from typing import Tuple
from flask import jsonify, Flask, render_template
from mod.exceptions import GrowingGrubsException
from mod.logging_config import get_logger
import uuid

logger = get_logger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register all error handlers with the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(GrowingGrubsException)
    def handle_growing_grubs_exception(error: GrowingGrubsException) -> Tuple[dict, int]:
        """Handle custom GrowingGrubs exceptions."""
        logger.warning(f"GrowingGrubs exception: {error.error_code} - {error.message}")
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error) -> Tuple:
        """Handle 400 Bad Request errors."""
        logger.warning(f"Bad request: {error}")
        return render_template('errors/400.html', details=str(error)), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error) -> Tuple:
        """Handle 401 Unauthorized errors."""
        logger.warning(f"Unauthorized access attempt")
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error) -> Tuple:
        """Handle 403 Forbidden errors."""
        logger.warning(f"Forbidden access attempt")
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def handle_not_found(error) -> Tuple:
        """Handle 404 Not Found errors."""
        logger.info(f"Resource not found: {error}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(409)
    def handle_conflict(error) -> Tuple[dict, int]:
        """Handle 409 Conflict errors."""
        logger.warning(f"Conflict error: {error}")
        return jsonify({
            'error': 'conflict',
            'message': 'The request conflicts with the current state of the resource',
            'status_code': 409
        }), 409
    
    @app.errorhandler(429)
    def handle_rate_limit(error) -> Tuple:
        """Handle 429 Rate Limit errors."""
        logger.warning(f"Rate limit exceeded")
        return render_template(
            'errors/429.html',
            retry_after=error.headers.get('Retry-After', 60)
        ), 429
    
    @app.errorhandler(500)
    def handle_internal_error(error) -> Tuple:
        """Handle 500 Internal Server errors."""
        error_id = str(uuid.uuid4())
        logger.error(f"Internal server error [ID: {error_id}]: {error}", exc_info=True)
        return render_template('errors/500.html', error_id=error_id), 500
    
    @app.errorhandler(503)
    def handle_service_unavailable(error) -> Tuple:
        """Handle 503 Service Unavailable errors."""
        logger.error(f"Service unavailable: {error}")
        return render_template('errors/503.html'), 503
