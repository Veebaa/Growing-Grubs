import json
from flask import url_for
from werkzeug.security import check_password_hash
from mod.models import db, Users, Recipe, Favourites, user_favourites
import requests


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
    assert b'Test Recipe' in response.data  # Check if the recipe title is displayed


def login_user(client, username, password):
    response = client.post(url_for('other_routes.login'), data={
        'username': username,
        'password': password
    }, follow_redirects=True)  # Follow redirects to check where it leads
    return response


# Test the profile route
def test_profile_route(client):
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


# Test successful registration
def test_successful_registration(client):
    response = client.post(url_for('other_routes.register_user'), data={
        'username': 'newuser',
        'first_name': 'New',
        'last_name': 'User',
        'email': 'newuser@example.com',
        'profile_image': 'avo.jpg',  # valid profile image choice
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'You have been successfully registered.' in response.data
    assert b'Login' in response.data

    # Check that the user was actually added to the database
    user = Users.query.filter_by(username='newuser').first()
    assert user is not None
    assert check_password_hash(user.password, 'password123')


def test_registration_missing_fields(client):
    response = client.post(url_for('other_routes.register_user'), data={
        'username': 'incompleteuser',
        'first_name': 'Incomplete',
        # Missing last_name, email, password, and confirm_password
        'profile_image': 'avo.jpg',
    }, follow_redirects=True)

    assert response.status_code == 200

    # Check for specific field validation error messages
    assert b'Last name required' in response.data
    assert b'Email required' in response.data
    assert b'Password required' in response.data
    assert b'Please select a profile image' not in response.data  # Since profile image is provided


# Test registration with duplicate username
def test_registration_duplicate_username(client):
    # First, create a user with the username
    client.post(url_for('other_routes.register_user'), data={
        'username': 'duplicateuser',
        'first_name': 'Duplicate',
        'last_name': 'User',
        'email': 'duplicateuser@example.com',
        'profile_image': 'avo.jpg',  # valid profile image choice
        'password': 'password123',
        'confirm_password': 'password123'  # corrected field name
    }, follow_redirects=True)

    # Try to create another user with the same username
    response = client.post(url_for('other_routes.register_user'), data={
        'username': 'duplicateuser',
        'first_name': 'Another',
        'last_name': 'User',
        'email': 'another@example.com',
        'profile_image': 'cherries.jpg',  # another valid profile image
        'password': 'password123',
        'confirm_password': 'password123'  # corrected field name
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Sorry! Username already in use.' in response.data  # updated to correct message


# Test registration with invalid email
def test_registration_invalid_email(client):
    response = client.post(url_for('other_routes.register_user'), data={
        'username': 'invalidemailuser',
        'first_name': 'Invalid',
        'last_name': 'Email',
        'email': 'invalidemail',  # Invalid email format
        'profile_image': 'default.jpg',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email address.' in response.data


# Test the search route
def test_search_route(client):
    response = client.post(url_for('other_routes.search'), data={'search': 'pasta'})
    assert response.status_code == 200
    assert b'pasta' in response.data


# Test meal detail route
def test_meal_detail_route(client):

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
    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200  # Ensure login was successful and followed redirect

    # Test logout response
    response = client.post(url_for('other_routes.logout'))  # Changed to POST request
    assert response.status_code == 302  # Assuming a redirect after logout


# Test route for deleting account
def test_delete_account_route(client):

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200  # Ensure login was successful and followed redirect

    # Test logout response
    response = client.post(url_for('other_routes.delete_account'))  # Changed to POST request
    assert response.status_code == 302  # Assuming a redirect after logout


# Test route for adding favourite
def test_favourite_recipe(client, db_session, sample_recipe):
    # Ensure sample user is already set up in conftest.py
    user = Users.query.filter_by(username='testuser').first()
    assert user is not None, "Test user should exist for the test to proceed."

    # Log in the sample user
    login_data = {
        'username': 'testuser',
        'password': 'password1234'
    }
    response = client.post('/login', data=login_data, follow_redirects=True)
    assert response.status_code == 200  # Ensure login was successful

    # Confirm session is active by accessing a protected route, e.g., /profile
    response = client.get('/profile')
    assert response.status_code == 200, "User should be able to access profile after login."

    # Prepare form data for favoriting the recipe
    form_data = {
        'recipe_title': sample_recipe.title,
        'recipe_image': 'test_image.jpg'
    }

    # Send POST request to add the recipe to the user's favorites
    response = client.post(
        f'/favourite/{sample_recipe.id}',
        data=form_data,
        follow_redirects=True  # Follow redirects to handle any login redirects
    )

    # Check for successful addition and flash message
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    assert b'Recipe added to favourites!' in response.data, "Flash message should be present in response."

    # Verify favorite in database
    favourited_recipe = db_session.query(Favourites).filter_by(recipe_id=sample_recipe.id).first()
    assert favourited_recipe is not None, "Favorite should be created in the database."
    assert favourited_recipe.recipe_title == sample_recipe.title
    assert favourited_recipe.recipe_image == form_data['recipe_image']


# Test route for removing favourite
def test_unfavourite_recipe(client):
    # Add a test recipe to the database
    recipe = Recipe(title='Test Recipe', description='A test recipe for unfavouriting.')
    db.session.add(recipe)
    db.session.commit()

    # Simulate user login
    login_response = login_user(client, 'testuser', 'password1234')
    assert login_response.status_code == 200

    # Get the test user from the database
    test_user = Users.query.filter_by(username='testuser').first()

    # Create a favourite entry
    favourite = Favourites(recipe_id=recipe.id, recipe_title=recipe.title, recipe_image='test_image.jpg')
    db.session.add(favourite)
    db.session.commit()

    # Associate the recipe as a favourite of the test user
    test_user.favourites.append(favourite)
    db.session.commit()

    # Simulate the unfavourite route
    client.post(url_for('other_routes.unfavourite_recipe', recipe_id=recipe.id), follow_redirects=True)

    # Check the association table after unfavouriting
    after_unfavourite = db.session.query(user_favourites).filter_by(user_id=test_user.id,
                                                                    favourite_id=favourite.id).first()

    # Verify the association removal
    assert after_unfavourite is None

    # Check if the favourite recipe is still in the Favourites table
    unfavourited_recipe = db.session.query(Favourites).filter_by(id=favourite.id).first()

    # Ensure the recipe was removed from the user's favourites list but still in the Favourites table
    assert unfavourited_recipe is not None


def test_healthy_eating_get(client):
    response = client.get(url_for('other_routes.healthy_eating'))
    assert response.status_code == 200
    assert b'Healthy Eating' in response.data  # Assuming 'Healthy Eating' is in the template


def test_healthy_eating_post(client):
    response = client.post(url_for('other_routes.healthy_eating'), data={'age_group': 'children'})
    assert response.status_code == 200
    assert b'Portion Sizes' in response.data  # Adjust based on the content of your template


def test_feeding_stages(client, sample_recipe):
    response = client.get(url_for('other_routes.feeding_stages'))
    assert response.status_code == 200
    assert b'Test Recipe' in response.data  # Assuming 'Test Recipe' is the top recipe


def test_signs(client, sample_recipe):
    response = client.get(url_for('other_routes.signs'))
    assert response.status_code == 200
    assert b'Test Recipe' in response.data  # Assuming 'Test Recipe' is the top recipe


def test_proxy_success(client, mocker):
    mock_response = {
        'branded': [
            {'food_name': 'Spring Mix Baby Lettuce, Baby Greens', 'brand_name': 'Organic Marketside',
             'serving_qty': 3, 'serving_unit': 'cups'},
            {'food_name': 'Baby-Cut Carrots', 'brand_name': 'Bolthouse Farms', 'serving_qty': 3, 'serving_unit': 'oz.'},
        ],
        'common': [
            {'food_name': 'apple', 'serving_qty': '1', 'serving_unit': 'unit'},
            {'food_name': 'banana', 'serving_qty': '1', 'serving_unit': 'unit'},
        ]
    }

    # Mock requests.get to return a successful response
    mock_get = mocker.patch('mod.app.requests.get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    response = client.get('/proxy?age_group=adults')

    print(response.data)  # Print the response data for debugging

    assert response.status_code == 200
    assert b'apple' in response.data
    assert b'banana' in response.data
    assert b'Spring Mix Baby Lettuce, Baby Greens' in response.data
    assert b'Baby-Cut Carrots' in response.data


# Test for missing age_group parameter
def test_proxy_missing_age_group(client):
    response = client.get('/proxy')

    assert response.status_code == 400
    assert b'Missing age_group parameter' in response.data


# Test for an HTTP error from the external API
def test_proxy_http_error(client, mocker):
    # Mock requests.get to raise an HTTPError
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = requests.exceptions.HTTPError

    response = client.get('/proxy?age_group=adults')

    assert response.status_code == 500
    assert b'HTTP error occurred' in response.data


# Test for a connection error
def test_proxy_connection_error(client, mocker):
    # Mock requests.get to raise a ConnectionError
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = requests.exceptions.ConnectionError

    response = client.get('/proxy?age_group=adults')

    assert response.status_code == 500
    assert b'Connection error occurred' in response.data


# Test for a timeout error
def test_proxy_timeout_error(client, mocker):
    # Mock requests.get to raise a Timeout
    mock_get = mocker.patch('requests.get')
    mock_get.side_effect = requests.exceptions.Timeout

    response = client.get('/proxy?age_group=adults')

    assert response.status_code == 500
    assert b'Request timed out' in response.data
