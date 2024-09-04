import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    application = Flask(__name__, static_folder='../static')
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Configure the app
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    application.config['SECRET_KEY'] = 'secret_key'
    application.config['WTF_CSRF_SECRET_KEY'] = 'your_csrf_secret_key'
    application.config['SESSION_TYPE'] = 'filesystem'
    application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the SQLAlchemy object with the app
    db.init_app(application)


    from mod.user_manager import init_login_manager
    init_login_manager(application)

    # Custom Jinja2 filter
    def yesno(value, yes='Yes', no='No'):
        return yes if value else no

    application.jinja_env.filters['yesno'] = yesno

    return application
