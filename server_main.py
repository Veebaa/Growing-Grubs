import logging
import os
import sys
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_migrate import upgrade

# Load environment variables early
from mod.env_loader import EnvLoader
EnvLoader.load_env_file()
EnvLoader.ensure_env_file_exists()

from mod import create_app
from mod.app import other_routes, debug_routes
from mod.user_manager import init_login_manager
from mod.logging_config import get_logger

# Create the Flask app
application = create_app()

# Get logger after app is created (uses centralized logging)
logger = get_logger(__name__)

with application.app_context():
    upgrade()

logger.info('Starting the Flask application...')
EnvLoader.print_config_summary()

# Blueprints are now registered in mod/__init__.py
# The following lines are no longer needed:
# application.register_blueprint(other_routes)
# application.register_blueprint(debug_routes)

# Initialize the login manager
init_login_manager(application)

# Define the search form
class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

# Make the search form available in all templates
@application.context_processor
def inject_search_form():
    return {'form': SearchForm()}


def main():
    """Start the Flask development server."""
    try:
        # Run the Flask server
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting server on port {port}")
        application.run(debug=application.config.get('DEBUG', False), host="0.0.0.0", port=port)

    except Exception as e:
        logger.error(f'Failed to start application: {e}', exc_info=True)
        raise


if __name__ == '__main__':
    main()
