import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='../static')

# Initialize the logger
logger = None

def yesno(value, yes='Yes', no='No'):
    return yes if value else no

app.jinja_env.filters['yesno'] = yesno

def create_app():
    global logger  # Logger is accessible globally
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SECRET_KEY'] = 'secret_key'
    app.config['WTF_CSRF_SECRET_KEY'] = 'your_csrf_secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    # Initialize logger
    logger = create_logger()
    return app

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
