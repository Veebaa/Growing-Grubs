from datetime import datetime
import pytest
from mod import create_app
from mod.models import db, Recipe, Users
from mod.app import other_routes


@pytest.fixture
def client():
    # Create a test configuration with an in-memory SQLite database
    app = create_app(test_config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'SERVER_NAME': 'localhost',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection for testing
    })

    app.register_blueprint(other_routes)

    with app.app_context():
        db.create_all()
        user = Users(username='testuser', first_name='testname', last_name='testlast', profile_image='avo.jpg',
                     email='test@example.com')
        user.set_password('password1234')  # Make sure the password is hashed correctly
        db.session.add(user)
        db.session.commit()
        yield app.test_client()
        db.drop_all()


def test_index_route(client, mocker):
    # Mock the get_topics_logic to avoid external API calls during testing
    mocker.patch('mod.app.get_topics_logic', return_value=[
        {'name': 'Test Article', 'description': 'This is a test article.', 'url': 'https://example.com'}
    ])

    # Add test recipe data
    recipe1 = Recipe(title='Recipe 1', views=10, last_viewed=datetime.utcnow())
    recipe2 = Recipe(title='Recipe 2', views=20, last_viewed=datetime.utcnow())
    db.session.add_all([recipe1, recipe2])
    db.session.commit()

    response = client.get('/')
    assert response.status_code == 200
    assert b'Test Article' in response.data  # Check for article rendering
    assert b'Recipe 2' in response.data  # Check if the top recipe is displayed


def test_no_top_recipe(client, mocker):
    # Mock the get_topics_logic to avoid external API calls during testing (for Top Stories)
    mocker.patch('mod.app.get_topics_logic', return_value=[])

    # Test the scenario where no recipes are added and no stories are available
    response = client.get('/')
    assert response.status_code == 200
    assert b'No stories available.' in response.data  # Check if "No stories" is displayed
