import json
from flask import url_for
from mod.models import db, Users, Recipe

# Test the debug route
def test_debug_route(client):
    response = client.get('/debug')
    assert response.status_code == 200
    assert b'debugging' in response.data


# Test the index route
def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Growing Grubs' in response.data

# Test the recipes route
def test_recipes_route(client, mocker):
    # Mock the get_topics_logic to avoid external API calls during testing
    mocker.patch('mod.app.get_topics_logic', return_value=[
        {'name': 'Test Article', 'description': 'This is a test article.', 'url': 'https://example.com'}
    ])

    # Add test recipe to the database
    recipe = Recipe(title='Test Recipe', description='This is a test recipe.')
    db.session.add(recipe)
    db.session.commit()

    response = client.get(url_for('other_routes.recipes'))
    assert response.status_code == 200
    assert b'Test Recipe' in response.data # Check if the recipe title is displayed


def login_user(client, username, password):
    response = client.post(url_for('other_routes.login'), data={
        'username': username,
        'password': password
    }, follow_redirects=True)  # Follow redirects to check where it leads
    return response


# Test the profile route
def test_profile_route(client):
    # Add test user to the database
    user = Users(username='testuser', first_name='testname', last_name='testlast', profile_image='avo.jpg',
                 email='test@example.com')
    user.set_password('password1234')
    db.session.add(user)
    db.session.commit()

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')

    # Debug: Print response data
    print("Login response data:", login_response.data.decode())

    # Ensure login was successful
    assert login_response.status_code == 200  # Check final response status code
    assert b'testuser' in login_response.data  # Check if user data is present


# Test the login route
def test_login_route(client):
    response = client.get(url_for('other_routes.login'))
    assert response.status_code == 200
    assert b'Login' in response.data

# Test the register route
def test_register_route(client):
    response = client.get(url_for('other_routes.register_user'))
    assert response.status_code == 200
    assert b'Register' in response.data

# Test the search route
def test_search_route(client):
    response = client.post(url_for('other_routes.search'), data={'search': 'pasta'})
    assert response.status_code == 200
    assert b'pasta' in response.data

# Test meal detail route
def test_meal_detail_route(client):
    # Add test user to the database
    user = Users(username='testuser', first_name='testname', last_name='testlast', profile_image='avo.jpg',
                 email='test@example.com', password='password1234')
    user.set_password('password1234')  # Make sure the password is hashed correctly
    db.session.add(user)
    db.session.commit()

    # Add test recipe to the database
    recipe = Recipe(title='Test Recipe', description='A detailed recipe for testing.',
                    image_url='/static/images/test.jpg', method=json.dumps(['Step 1: Test']),
                    ingredients=json.dumps(['Ingredient 1', 'Ingredient 2']))
    db.session.add(recipe)
    db.session.commit()

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200  # Ensure login was successful and followed redirect

    # Access the meal_detail route
    response = client.get(url_for('other_routes.meal_detail', meal_id=recipe.id), follow_redirects=True)

    # Ensure the response is 200 OK and contains the test recipe details
    assert response.status_code == 200
    assert b'Test Recipe' in response.data
    assert b'Step 1: Test' in response.data
    assert b'Ingredient 1' in response.data

# Test route for editing a user profile
def test_edit_profile_route(client):
    # Add test user to the database
    user = Users(username='testuser', first_name='testname', last_name='testlast', profile_image='avo.jpg',
                 email='test@example.com')
    user.set_password('password1234')  # Make sure the password is hashed correctly
    db.session.add(user)
    db.session.commit()

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200  # Ensure login was successful and followed redirect

    # Test profile update
    response = client.post(url_for('other_routes.edit_profile'), data={
        'first_name': 'updatedname',
        'last_name': 'updatedlast',
        'email': 'updated@example.com',
        'profile_image': 'updated_image.jpg'
    })
    assert response.status_code == 302  # Assuming a redirect after update

    # Verify the updates in the database
    updated_user = Users.query.filter_by(username='testuser').first()
    assert updated_user.first_name == 'updatedname'
    assert updated_user.last_name == 'updatedlast'
    assert updated_user.email == 'updated@example.com'
    assert updated_user.profile_image == 'updated_image.jpg'


# Test route for logging out
def test_logout_route(client):
    # Add test user to the database
    user = Users(username='testuser', first_name='testname', last_name='testlast', profile_image='avo.jpg',
                 email='test@example.com')
    user.set_password('password1234')  # Make sure the password is hashed correctly
    db.session.add(user)
    db.session.commit()

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200  # Ensure login was successful and followed redirect

    # Test logout response
    response = client.post(url_for('other_routes.logout'))  # Changed to POST request
    assert response.status_code == 302  # Assuming a redirect after logout



