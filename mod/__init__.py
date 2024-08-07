import logging
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='../static')
logger = logging.getLogger('growing_grubs_logger')


def yesno(value, yes='Yes', no='No'):
    return yes if value else no


app.jinja_env.filters['yesno'] = yesno


def create_app():
    create_logger()
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SECRET_KEY'] = 'secret_key'
    app.config['WTF_CSRF_SECRET_KEY'] = 'your_csrf_secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def create_logger():
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

