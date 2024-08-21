from mod import db, create_app, logger
from flask_migrate import Migrate
from app import other_routes


def main():
    try:
        # Create the app and initialize the logger
        app = create_app()
        app.register_blueprint(other_routes)
        app.app_context().push()
        # Perform migrations
        db.create_all()
        migrate = Migrate(app, db)
        # Start the Flask server
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.error(f'Failed to get config and create application: {e}', exc_info=True)


if __name__ == '__main__':
    main()
