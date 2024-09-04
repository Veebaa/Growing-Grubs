import logging
from mod import create_app, db
from flask_migrate import Migrate
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


def main():
    try:
        # Create the app and initialize the logger
        application = create_app()
        application.logger = create_logger()  # Set the logger in the app

        application.register_blueprint(other_routes)

        # Initialize the login manager here
        init_login_manager(application)

        # Set up Flask-Migrate
        migrate = Migrate(application, db)

        # Log application start
        application.logger.info('Starting the Flask application...')
        # Run the Flask server
        application.run(debug=True, port=5000)

    except Exception as e:
        # Initialize logger
        logger = create_logger()  # Use create_logger() to get the logger
        logger.error(f'Failed to get config and create application: {e}', exc_info=True)

if __name__ == '__main__':
    main()
