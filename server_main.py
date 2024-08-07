from flask import Blueprint
from flask_login import LoginManager

from mod import db, create_app, logger
from flask_migrate import Migrate
from app import other_routes


def main():
    try:
        app = create_app()
        app.register_blueprint(other_routes)
        app.app_context().push()
        db.create_all()
        migrate = Migrate(app, db)
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.error(f'Failed to get config and create application: {e}', exc_info=True)


if __name__ == '__main__':
    main()
