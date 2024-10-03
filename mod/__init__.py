import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()


def create_app(test_config=None):
    application = Flask(__name__, static_folder='../static')
    basedir = os.path.abspath(os.path.dirname(__file__))
    migrate = Migrate(application, db)
    csrf = CSRFProtect(application)

    # Default configuration
    application.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'database.db'),
        SECRET_KEY='secret_key',
        WTF_CSRF_SECRET_KEY='your_csrf_secret_key',
        SESSION_TYPE='filesystem',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Apply test configuration if provided
    if test_config:
        application.config.from_mapping(test_config)

    # Initialize the SQLAlchemy object with the app
    db.init_app(application)

    from mod.user_manager import init_login_manager
    init_login_manager(application)

    # Custom Jinja2 filter
    def yesno(value, yes='Yes', no='No'):
        return yes if value else no

    application.jinja_env.filters['yesno'] = yesno

    return application
