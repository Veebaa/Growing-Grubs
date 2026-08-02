"""
Pytest configuration and shared fixtures for Growing Grubs tests.

This module provides common fixtures and configuration for all tests.
"""

import os
import tempfile
import pytest
from mod import create_app, db
from mod.models import Users, Recipe


@pytest.fixture
def app():
    """Create and configure a test Flask app."""
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with testing config
    test_config = {
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'TESTING': True
    }
    app = create_app(test_config=test_config)
    
    # Create tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    """Create an authenticated test client."""
    with app.app_context():
        # Create a test user
        user = Users(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            profile_image='default.jpg'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    return client


@pytest.fixture
def sample_recipe(app):
    """Create a sample recipe for testing."""
    with app.app_context():
        recipe = Recipe(
            title='Test Recipe',
            description='A test recipe',
            ingredients='Ingredient 1, Ingredient 2',
            method='Mix and cook',
            age_group='1-3 years',
            dietary_info='Nutritious'
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = Users(
            username='sampleuser',
            email='sample@example.com',
            first_name='Sample',
            last_name='User',
            profile_image='default.jpg'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def app_context(app):
    """Provide app context for tests that need it."""
    with app.app_context():
        yield app


class MockResponse:
    """Mock response object for testing API calls."""
    
    def __init__(self, json_data=None, status_code=200):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.headers = {}
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_response():
    """Provide mock response for API testing."""
    return MockResponse


# Pytest hooks
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Auto-mark tests based on file path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
