import logging
import os
import sys
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_migrate import upgrade

from mod import create_app
from mod.app import other_routes
from mod.user_manager import init_login_manager


def create_logger():
    # Create a logger object
    logger = logging.getLogger('growing_grubs_logger')
    logger.setLevel(logging.DEBUG)  # DEBUG to capture all log levels

    # Create a file handler to log messages to a file
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)  # Log everything to the file

    # Create a console handler to log messages to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log INFO and above to the console

    # Create a formatter and set it for the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create the Flask app
application = create_app()

with application.app_context():
    upgrade()

application.logger = create_logger()  # Set the logger in the app

application.register_blueprint(other_routes)

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

# Log application start
application.logger.info('Starting the Flask application...')

def main():
    try:
        # Run the Flask server
        port = int(os.environ.get("PORT", 10000))
        application.run(debug=False, host="0.0.0.0", port=port)
        sys.stdout.reconfigure(line_buffering=True)

    except Exception as e:
        # Initialize logger
        logger = create_logger()  # Use create_logger() to get the logger
        logger.error(f'Failed to get config and create application: {e}', exc_info=True)


if __name__ == '__main__':
    main()
