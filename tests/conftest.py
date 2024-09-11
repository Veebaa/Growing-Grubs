import pytest
from mod import create_app
from mod.models import db, Recipe


@pytest.fixture
def client():
    # Create a test configuration with an in-memory SQLite database
    app = create_app(test_config={
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'SERVER_NAME': 'localhost',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection for testing
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_index_route(client, mocker):
    # Mock the get_topics_logic to avoid external API calls during testing
    mocker.patch('mod.other_routes.get_topics_logic', return_value=[
        {'name': 'Test Article', 'description': 'This is a test article.', 'url': 'https://example.com'}
    ])

    # Add test recipe data
    recipe1 = Recipe(title='Recipe 1', views=10, last_viewed='2024-09-10')
    recipe2 = Recipe(title='Recipe 2', views=20, last_viewed='2024-09-11')
    db.session.add_all([recipe1, recipe2])
    db.session.commit()

    response = client.get('/')
    assert response.status_code == 200
    assert b'Test Article' in response.data  # Check for article rendering
    assert b'Recipe 2' in response.data  # Check if the top recipe is displayed


def test_no_top_recipe(client, mocker):
    # Mock the get_topics_logic to avoid external API calls during testing (for Top Stories)
    mocker.patch('mod.other_routes.get_topics_logic', return_value=[])

    # Test the scenario where no recipes are added and no stories are available
    response = client.get('/')
    assert response.status_code == 200
    assert b'No stories available.' in response.data  # Check if "No stories" is displayed

