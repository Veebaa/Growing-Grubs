import json
import requests
import logging
import random
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from mod import db
from mod.models import Users, Favourites, user_favourites, Recipe
from mod.user_manager import RegistrationForm, LoginForm
from datetime import datetime, timedelta

other_routes = Blueprint("other_routes", __name__, static_folder='static', template_folder='../templates')

if logging.getLogger('growing_grubs_logger') is None:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('growing_grubs_logger')

@other_routes.route('/debug')
def debug():
    return jsonify({'status': 'debugging'})


@other_routes.route("/")
def index():
    # Fetch the top stories articles
    articles = get_topics_logic()
    # Top recipe function
    # Calculate the date for the previous day
    yesterday = datetime.now() - timedelta(days=1)
    start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
    end_of_yesterday = datetime.combine(yesterday, datetime.max.time())
    # Get the most viewed recipe from the previous day
    top_recipe = Recipe.query.filter(Recipe.last_viewed >= start_of_yesterday,
                                     Recipe.last_viewed <= end_of_yesterday)\
                             .order_by(Recipe.views.desc())\
                             .first()

    if not top_recipe:
        # Fallback to the most viewed recipe of all time if no recipe was viewed yesterday
        top_recipe = Recipe.query.order_by(Recipe.views.desc()).first()

    return render_template("index.html", articles=articles, top_recipe=top_recipe)

def get_topics_logic():
    api_key = '4cf8144bb46d4122b603ebcadbd688cc'
    endpoint = 'https://api.nhs.uk/conditions'
    headers = {
        'subscription-key': api_key,
        'Content-Type': 'application/json'
    }
    logger = current_app.logger
    try:
        response = requests.get(endpoint, headers=headers, params={'topic':'children development, childhood illness'})
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get('significantLink', []):
            name = item.get('name', 'No Title')
            description = item.get('description', 'No Description')
            url = item.get('url', '#')
            articles.append({'name': name,'description': description, 'url': url})

        if len(articles) >= 2:
            logger.info(articles) #  Log random articles
            return random.sample(articles, 2)
        else:
            return articles

    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching data from NHS API: {e}")
        return []


@other_routes.route('/register', methods=['GET', 'POST'])
def register_user():
    # Create an instance of RegistrationForm to handle user registration
    form = RegistrationForm()
    # Get the current logger instance for logging information
    logger = current_app.logger

    # Check if the form was submitted and is valid
    if form.validate_on_submit():
        logger.info(f"Registering new User {form.username.data}")
        try:
            # Create a new user instance with the form data
            user = Users(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                profile_image=form.profile_image.data
            )
            # Hash the password before storing it
            user.set_password(form.password.data)
            # Add the new user to the session
            db.session.add(user)
            # Commit the transaction to save the user to the database
            db.session.commit()

            logger.info(f"User {form.username.data} registered successfully!")
            # Redirect the user to the login page after successful registration
            return redirect(url_for('other_routes.login'))

        except SQLAlchemyError as e:
            # Log an error if the registration fails and roll back the session
            logger.error("Registration failed!")
            db.session.rollback()
            return f"Commit failed. Error: {e}"

    # Render the registration form template if the form is not submitted or invalid
    return render_template('register_user.html', title='Register', form=form)


@other_routes.route('/login', methods=['GET', 'POST'])
def login():
    # Get the current logger instance for logging information
    logger = current_app.logger

    # Redirect the user to their profile page if they are already authenticated
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} is authenticated. Redirecting to profile page.')
        return redirect(url_for('other_routes.profile'))

    # Create an instance of LoginForm to handle user login
    form = LoginForm()

    # Check if the form was submitted and is valid
    if form.validate_on_submit():
        # Retrieve the user by username
        user = Users.query.filter_by(username=form.username.data).first()
        # Check if the user exists and if the password is correct
        if user is None or not user.check_password(form.password.data):
            # Flash an error message if the login fails
            flash('Invalid username or password')
            return redirect(url_for('other_routes.login'))

        # Log the user in and remember their session based on the form input
        login_user(user, remember=form.remember.data)
        logger.info(f'User {user.username} logged in successfully.')

        # Redirect to the 'next' parameter if it exists (e.g., from a protected route)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        else:
            logger.info(f'Redirecting user {user.username} to profile page.')
            return redirect(url_for('other_routes.profile'))

    # Render the login form template if the form is not submitted or invalid
    return render_template('login.html', title='Log In', form=form)


@other_routes.route('/logout', methods=['POST'])
@login_required
def logout():
    # Log the user out
    logout_user()
    # Flash a message indicating successful logout
    flash("You have been logged out.")
    # Redirect the user to the index page
    return redirect(url_for('other_routes.index'))


@other_routes.route('/profile')
@login_required
def profile():
    # Get the current logger instance for logging information
    logger = current_app.logger

    # Define a list of available profile images for the user to select
    available_profile_images = ['avo.jpg', 'cherries.jpg', 'orange.jpg', 'strawberry.jpg', 'watermelon.jpg']

    # Create a dictionary with the current user's profile information
    user_info = {
        'profile_image': current_user.profile_image,
        'username': current_user.username,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'email': current_user.email,
        'favourites': current_user.favourites
    }

    # Log the user's favourites for debugging purposes
    logger.info(f"User favourites: {user_info['favourites']}")

    # Render the profile template with user information and available profile images
    return render_template('profile.html', user=user_info, available_profile_images=available_profile_images)


@other_routes.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    # Retrieve the updated profile information from the request form
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    profile_image = request.form.get('profile_image')

    try:
        # Update the current user's profile information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.profile_image = profile_image

        # Commit the transaction to save the updated information to the database
        db.session.commit()
        flash('Profile updated successfully!')
    except Exception as e:
        # Roll back the session and flash an error message if the update fails
        db.session.rollback()
        flash('Error updating profile: ' + str(e))

    # Redirect the user back to their profile page after the update
    return redirect(url_for('other_routes.profile'))


@other_routes.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Get the current user to be deleted
    user = current_user
    try:
        # Delete the user from the database
        db.session.delete(user)
        # Commit the transaction to remove the user
        db.session.commit()
        # Log out the user and flash a success message
        logout_user()
        flash('Your account has been successfully deleted.', 'success')
        # Redirect the user to the index page after account deletion
        return redirect(url_for('other_routes.index'))
    except Exception as e:
        # Roll back the session and flash an error message if the deletion fails
        db.session.rollback()
        flash('An error occurred while deleting your account. Please try again later.', 'danger')
        # Redirect the user back to their profile page
        return redirect(url_for('other_routes.profile'))


def paginate_recipes(recipes_query=None, keywords=None, template_name=None, search_query=None):
    # If no query object is provided, start a new query
    if recipes_query is None:
        recipes_query = Recipe.query

    # Apply keyword filtering if keywords are provided
    if keywords:
        recipes_query = recipes_query.filter(Recipe.age_group.in_(keywords))

    # Pagination parameters
    per_page = 15  # Number of recipes to display per page
    page = request.args.get('page', 1, type=int)  # Get the current page number from query parameters, default to 1

    try:
        # Get paginated results, ordering recipes by title in ascending order
        pagination = recipes_query.order_by(Recipe.title.asc()).paginate(page=page, per_page=per_page, error_out=False)
        recipes = pagination.items  # List of recipes on the current page
        total_pages = pagination.pages  # Total number of pages
        next_page = pagination.next_num if pagination.has_next else None  # Number of the next page, if it exists
        prev_page = pagination.prev_num if pagination.has_prev else None  # Number of the previous page, if it exists

        # Convert recipes to a serializable format (e.g., dictionary) for easier rendering in templates
        recipes_list = [recipe.to_dict() for recipe in recipes]

        # Return a dictionary of pagination data to be used in rendering
        return {
            'recipes': recipes_list,
            'next_page': next_page,
            'prev_page': prev_page,
            'current_page': page,
            'total_pages': total_pages,
            'search_query': search_query  # Include the search query in the returned data for reference
        }
    except Exception as e:
        # Log any unexpected errors that occur during pagination
        logger = current_app.logger
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        # Return a default dictionary with empty results and pagination info
        return {
            'recipes': [],
            'next_page': None,
            'prev_page': None,
            'current_page': 1,
            'total_pages': 1,
            'search_query': search_query
        }


@other_routes.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    # Fetch the recipe by its ID from the database
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        abort(404)  # Return a 404 error if the recipe is not found

    # Log the view for the recipe
    recipe.log_view()

    # Render the recipe detail template with the fetched recipe
    return render_template('meal_detail.html', recipe=recipe)


@other_routes.route('/recipes')
def recipes():
    # Fetch articles for the page
    articles = get_topics_logic()

    # Fetch paginated recipes with the base query for all recipes
    paginated_recipes = paginate_recipes(
        recipes_query=Recipe.query,  # Base query to retrieve recipes
        template_name='recipes.html'
    )

    # Render the recipes template with the pagination data and articles
    return render_template(
        'recipes.html',
        recipes=paginated_recipes['recipes'],  # Extract the list of recipes
        next_page=paginated_recipes['next_page'],
        prev_page=paginated_recipes['prev_page'],
        current_page=paginated_recipes['current_page'],
        total_pages=paginated_recipes['total_pages'],
        search_query=paginated_recipes['search_query'],
        articles=articles  # Pass the articles to the template
    )


@other_routes.route('/recipes1')
def recipes1():
    # Fetch articles for the page
    articles = get_topics_logic()
    # Define keywords for filtering recipes
    keywords = ["6Months", "4to6Months", "9Months", "7Months"]
    # Fetch paginated recipes with the specified keywords
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes1.html')

    # Render the recipes1 template with the pagination data and articles
    return render_template(
        'recipes1.html',
        recipes=paginated_recipes['recipes'],
        next_page=paginated_recipes['next_page'],
        prev_page=paginated_recipes['prev_page'],
        current_page=paginated_recipes['current_page'],
        total_pages=paginated_recipes['total_pages'],
        search_query=paginated_recipes['search_query'],
        articles=articles
    )


@other_routes.route('/recipes2')
def recipes2():
    # Fetch articles for the page
    articles = get_topics_logic()
    # Define keywords for filtering recipes
    keywords = ["9Months", "12Months", "10Months"]
    # Fetch paginated recipes with the specified keywords
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes2.html')

    # Render the recipes2 template with the pagination data and articles
    return render_template(
        'recipes2.html',
        recipes=paginated_recipes['recipes'],
        next_page=paginated_recipes['next_page'],
        prev_page=paginated_recipes['prev_page'],
        current_page=paginated_recipes['current_page'],
        total_pages=paginated_recipes['total_pages'],
        search_query=paginated_recipes['search_query'],
        articles=articles
    )


@other_routes.route('/recipes3')
def recipes3():
    # Fetch articles for the page
    articles = get_topics_logic()
    # Define keywords for filtering recipes
    keywords = ["12Months", "forTheWholeFamily"]
    # Fetch paginated recipes with the specified keywords
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes3.html')

    # Render the recipes3 template with the pagination data and articles
    return render_template(
        'recipes3.html',
        recipes=paginated_recipes['recipes'],
        next_page=paginated_recipes['next_page'],
        prev_page=paginated_recipes['prev_page'],
        current_page=paginated_recipes['current_page'],
        total_pages=paginated_recipes['total_pages'],
        search_query=paginated_recipes['search_query'],
        articles=articles
    )


@other_routes.route('/feeding_stages')
def feeding_stages():
    # Calculate the date for the previous day
    yesterday = datetime.now() - timedelta(days=1)
    start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
    end_of_yesterday = datetime.combine(yesterday, datetime.max.time())

    # Get the most viewed recipe from the previous day
    top_recipe = Recipe.query.filter(Recipe.last_viewed >= start_of_yesterday,
                                     Recipe.last_viewed <= end_of_yesterday) \
        .order_by(Recipe.views.desc()) \
        .first()

    if not top_recipe:
        # Fallback to the most viewed recipe of all time if no recipe was viewed yesterday
        top_recipe = Recipe.query.order_by(Recipe.views.desc()).first()

    # Render the feeding stages template with the top recipe
    return render_template('feeding_stages.html', top_recipe=top_recipe)


@other_routes.route('/signs')
def signs():
    # Calculate the date for the previous day
    yesterday = datetime.now() - timedelta(days=1)
    start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
    end_of_yesterday = datetime.combine(yesterday, datetime.max.time())

    # Get the most viewed recipe from the previous day
    top_recipe = Recipe.query.filter(Recipe.last_viewed >= start_of_yesterday,
                                     Recipe.last_viewed <= end_of_yesterday) \
        .order_by(Recipe.views.desc()) \
        .first()

    if not top_recipe:
        # Fallback to the most viewed recipe of all time if no recipe was viewed yesterday
        top_recipe = Recipe.query.order_by(Recipe.views.desc()).first()

    # Render the signs template with the top recipe
    return render_template('signs.html', top_recipe=top_recipe)


@other_routes.route('/search', methods=['POST'])
def search():
    # Get the search term from the request form
    search_term = request.form.get('search')
    # Fetch articles for the page
    articles = get_topics_logic()

    logger = current_app.logger
    logger.info(f"Searching for recipes with query: {search_term}")

    if not search_term:
        # Flash an error message and redirect if no search term is provided
        flash("Please enter a search term.")
        return redirect(url_for('other_routes.recipes'))

    try:
        # Perform the search in the database for recipes matching the search term in title or age group
        recipes_query = Recipe.query.filter(
            Recipe.title.ilike(f"%{search_term}%") |
            Recipe.age_group.ilike(f"%{search_term}%")
        )

        # Pass the pre-filtered query to the paginate_recipes function for pagination
        pagination_data = paginate_recipes(recipes_query=recipes_query, template_name='search_results.html',
                                           search_query=search_term)

        # Render the search results template with the pagination data and articles
        return render_template('search_results.html', **pagination_data, articles=articles)

    except Exception as e:
        # Log any errors during the search process and flash an error message
        logger.error(f"Error processing the search: {e}", exc_info=True)
        flash("An error occurred while searching for recipes.")
        return redirect(url_for('other_routes.recipes'))


@other_routes.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    # Fetch the top stories articles using the logic defined in get_topics_logic
    articles = get_topics_logic()

    # Get the current logger instance from the Flask app for logging information
    logger = current_app.logger
    logger.info(f"Fetching details for meal ID: {meal_id}")

    try:
        # Use a context manager to perform operations without auto-flushing changes
        with db.session.no_autoflush:
            # Retrieve the meal information from the database by primary key (meal_id)
            meal_info = db.session.get(Recipe, meal_id)

            # Check if the meal information was found
            if not meal_info:
                # Log an error if the meal ID is not found and return a 404 page
                logger.error(f"Meal ID {meal_id} not found in the database.")
                return render_template('404.html'), 404

            # Log the view of the meal (e.g., increment view count)
            meal_info.log_view()

            # Check if 'no_flush' parameter is set in the request arguments
            no_flush = request.args.get('no_flush') == 'true'

            if not no_flush:
                # Commit the session if no_flush is not true
                db.session.commit()
            else:
                # Flush the session (send changes to the database) if no_flush is true
                db.session.flush()

            # Ensure the image URL is not None; set a default image if it is
            meal_info.image_url = meal_info.image_url or '/static/images/default-recipe.jpg'
            # Provide a default message if the method (instructions) is None
            meal_info.method = meal_info.method or 'No instructions provided.'

            # Try to parse the ingredients JSON data; default to an empty list if parsing fails
            try:
                meal_info.ingredients = json.loads(meal_info.ingredients)
            except (json.JSONDecodeError, TypeError):
                meal_info.ingredients = []

            # Try to parse the method JSON data; default to an empty list if parsing fails
            try:
                meal_info.method = json.loads(meal_info.method)
            except (json.JSONDecodeError, TypeError):
                meal_info.method = []

            # Log successful retrieval of meal details
            logger.info(f"Successfully retrieved details for meal ID: {meal_id}")
            # Render the meal detail template with the meal information and articles
            return render_template('meal_detail.html', meal=meal_info, articles=articles)

    except Exception as e:
        # Log any unexpected errors and roll back the database session
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        db.session.rollback()
        # Return a 404 page in case of an unexpected error
        return render_template('404.html'), 404


@other_routes.route('/favourite/<int:recipe_id>', methods=['POST'])
@login_required
def favourite_recipe(recipe_id):
    user_id = current_user.id  # Get the ID of the currently logged-in user

    # Check if the recipe is already in the user's favourites
    existing_favourite = db.session.query(Favourites).join(user_favourites).filter(
        user_favourites.c.user_id == user_id,  # Ensure the user is the current user
        user_favourites.c.favourite_id == Favourites.id,  # Ensure the favourite matches the recipe
        Favourites.recipe_id == recipe_id  # Check if the recipe_id matches
    ).first()

    if existing_favourite is None:
        # If the recipe is not already a favourite, add it to the favourites
        recipe_title = request.form['recipe_title']  # Get recipe title from form data
        recipe_image = request.form['recipe_image']  # Get recipe image URL from form data
        new_favourite = Favourites(recipe_id=recipe_id, recipe_title=recipe_title, recipe_image=recipe_image)
        db.session.add(new_favourite)  # Add new favourite to the database
        db.session.commit()  # Commit the changes to the database

        # Associate the new favourite with the current user
        current_user.favourites.append(new_favourite)
        db.session.commit()  # Commit the changes to the database

        flash('Recipe added to favourites!', 'success')  # Notify the user of success
    else:
        flash('Recipe already in favourites.', 'info')  # Notify the user if the recipe is already a favourite

    return redirect(url_for('other_routes.profile'))  # Redirect to the user's profile page


@other_routes.route('/unfavourite/<int:recipe_id>', methods=['POST'])
@login_required
def unfavourite_recipe(recipe_id):
    user_id = current_user.id  # Get the ID of the currently logged-in user

    # Find the favourite recipe record to remove
    favourite = db.session.query(Favourites).join(user_favourites).filter(
        user_favourites.c.user_id == user_id,  # Ensure the user is the current user
        user_favourites.c.favourite_id == Favourites.id,  # Ensure the favourite matches the recipe
        Favourites.recipe_id == recipe_id  # Check if the recipe_id matches
    ).first()

    if favourite:
        # If the favourite is found, remove it from the user's favourites
        current_user.favourites.remove(favourite)  # Remove the favourite association
        db.session.commit()  # Commit the changes to the database
        flash('Recipe removed from favourites!', 'success')  # Notify the user of success
    else:
        flash('Recipe not found in favourites.', 'error')  # Notify the user if the recipe is not in favourites

    return redirect(url_for('other_routes.profile'))  # Redirect to the user's profile page


@other_routes.route('/healthy_eating', methods=['GET', 'POST'])
def healthy_eating():
    articles = get_topics_logic()  # Fetch articles for the page
    age_group = request.form.get('age_group')  # Get the age group from form data (if available)
    portion_sizes = []

    if age_group:
        # If an age group is specified, get portion sizes for that age group
        portion_sizes = get_portion_sizes(age_group)

    # Render the healthy eating template with portion sizes, age group, and articles
    return render_template('healthy_eating.html', portion_sizes=portion_sizes, age_group=age_group, articles=articles)


def get_portion_sizes(age_group):
    portions_api_key = '4f704df26c022d7001e8c639f94ed667'  # API key for Nutritionix
    app_id = 'c51d8bff'  # App ID for Nutritionix
    headers = {
        'x-app-id': app_id,
        'x-app-key': portions_api_key,
        'Content-Type': 'application/json'
    }

    query = f'{age_group} food'  # Query for food items related to the age group
    endpoint = 'https://trackapi.nutritionix.com/v2/search/instant'  # Nutritionix API endpoint
    params = {'query': query}  # Query parameters for the API request

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)  # Make the API request
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Parse the response JSON
        print(data)  # Debugging log to check the API response

        # Extract food items from the response
        foods = data.get('branded', []) + data.get('common', [])
        portion_sizes = [{
            'food_name': food['food_name'],  # Food name
            'serving_qty': food.get('serving_qty', 'N/A'),  # Serving quantity (if available)
            'serving_unit': food.get('serving_unit', 'N/A')  # Serving unit (if available)
        } for food in foods]

        return portion_sizes
    except requests.exceptions.RequestException as e:
        print(f'Error fetching portion sizes: {e}')  # Log the error
        return []  # Return an empty list in case of an error


@other_routes.errorhandler(404)
def not_found_error(error):
    # Render a 404 error page if a route is not found
    return render_template('404.html'), 404


@other_routes.route('/proxy', methods=['GET'])
def proxy():
    age_group = request.args.get('age_group')  # Get the age group from query parameters
    print(f'Received age_group parameter: {age_group}')  # Debugging log to check the received parameter

    # If no age_group is provided, return a 400 error
    if not age_group:
        return jsonify({'error': 'Missing age_group parameter'}), 400

    url = 'https://trackapi.nutritionix.com/v2/search/instant'  # Nutritionix API endpoint
    headers = {
        'x-app-id': 'c51d8bff',  # App ID for Nutritionix
        'x-app-key': '4f704df26c022d7001e8c639f94ed667',  # API key for Nutritionix
        'Content-Type': 'application/json'
    }
    params = {'query': age_group}  # Query parameters for the API request

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)  # Make the API request
        response.raise_for_status()  # Raise an exception for HTTP errors
        return jsonify(response.json())  # Return the JSON response from the API
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Log HTTP errors
        print(f'Response content: {response.content}')  # Log the response content
        return jsonify({'error': 'HTTP error occurred'}), 500
    except requests.exceptions.ConnectionError as conn_err:
        print(f'Connection error occurred: {conn_err}')  # Log connection errors
        return jsonify({'error': 'Connection error occurred'}), 500
    except requests.exceptions.Timeout as timeout_err:
        print(f'Timeout error occurred: {timeout_err}')  # Log timeout errors
        return jsonify({'error': 'Request timed out'}), 500
    except requests.exceptions.RequestException as req_err:
        print(f'Request error occurred: {req_err}')  # Log general request errors
        return jsonify({'error': 'Request error occurred'}), 500
    except Exception as err:
        print(f'Other error occurred: {err}')  # Log any other errors
        return jsonify({'error': 'An error occurred'}), 500
