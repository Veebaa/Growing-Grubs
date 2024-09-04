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


@other_routes.route("/")
def index():
    # Fetch the articles
    articles = get_topics_logic()  # Reuse get_topics logic
    return render_template("index.html", articles=articles)

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
    form = RegistrationForm()
    logger = current_app.logger
    if form.validate_on_submit():
        logger.info(f"Registering new User {form.username.data}")
        try:
            user = Users(username=form.username.data, first_name=form.first_name.data,
                         last_name=form.last_name.data, email=form.email.data, profile_image=form.profile_image.data)
            user.set_password(form.password.data)  # Hash the password
            db.session.add(user)
            db.session.commit()

            logger.info(f"User {form.username.data} registered successfully!")
            return redirect(url_for('other_routes.login'))

        except SQLAlchemyError as e:
            logger.error("Registration failed!")
            db.session.rollback()
            return f"Commit failed. Error: {e}"

    return render_template('register_user.html', title='Register', form=form)


@other_routes.route('/login', methods=['GET', 'POST'])
def login():
    logger = current_app.logger
    if current_user.is_authenticated:
        logger.info(f'User {current_user.username} is authenticated. Redirecting to profile page.')
        return redirect(url_for('other_routes.profile'))

    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')  # Flash the error message
            return redirect(url_for('other_routes.login'))  # Redirect back to login

        login_user(user, remember=form.remember.data)
        logger.info(f'User {user.username} logged in successfully.')

        next_page = request.args.get('next')  # Get the 'next' parameter
        if next_page:  # User tried to access a protected route
            return redirect(next_page)
        else:
            logger.info(f'Redirecting user {user.username} to profile page.')
            return redirect(next_page) if next_page else redirect(url_for('other_routes.profile'))  # Redirect to profile page

    return render_template('login.html', title='Log In', form=form)


@other_routes.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('other_routes.index'))


@other_routes.route('/profile')
@login_required
def profile():
    logger = current_app.logger
    available_profile_images = ['avo.jpg', 'cherries.jpg', 'orange.jpg', 'strawberry.jpg', 'watermelon.jpg']
    user_info = {
        'profile_image': current_user.profile_image,
        'username': current_user.username,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'email': current_user.email,
        'favourites': current_user.favourites
    }
    logger.info(f"User favourites: {user_info['favourites']}")
    return render_template('profile.html', user=user_info, available_profile_images=available_profile_images)


@other_routes.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    profile_image = request.form.get('profile_image')

    try:
        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.profile_image = profile_image

        db.session.commit()
        flash('Profile updated successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile: ' + str(e))

    return redirect(url_for('other_routes.profile'))

def paginate_recipes(recipes_query=None, keywords=None, template_name=None, search_query=None):
    # If no query object is provided, start a new query
    if recipes_query is None:
        recipes_query = Recipe.query

    # Apply keyword filtering if keywords are provided
    if keywords:
        recipes_query = recipes_query.filter(Recipe.age_group.in_(keywords))

    # Pagination parameters
    per_page = 15
    page = request.args.get('page', 1, type=int)

    try:
        # Get paginated results
        pagination = recipes_query.order_by(Recipe.title.asc()).paginate(page=page, per_page=per_page, error_out=False)
        recipes = pagination.items
        total_pages = pagination.pages
        next_page = pagination.next_num if pagination.has_next else None
        prev_page = pagination.prev_num if pagination.has_prev else None

        # Convert recipes to a serializable format
        recipes_list = [recipe.to_dict() for recipe in recipes]

        # Return a dictionary of pagination data
        return {
            'recipes': recipes_list,
            'next_page': next_page,
            'prev_page': prev_page,
            'current_page': page,
            'total_pages': total_pages,
            'search_query': search_query
        }
    except Exception as e:
        logger = current_app.logger
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
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
    # Fetch the recipe by ID
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        abort(404)  # Recipe not found

    # Log the view
    recipe.log_view()

    return render_template('meal_detail.html', recipe=recipe)


@other_routes.route('/recipes')
def recipes():
    # Fetch articles
    articles = get_topics_logic()

    # Fetch paginated recipes
    paginated_recipes = paginate_recipes(
        recipes_query=Recipe.query,  # Assuming this is your base query for recipes
        template_name='recipes.html'
    )

    # Render the template with both articles and recipes
    return render_template(
        'recipes.html',
        recipes=paginated_recipes['recipes'],  # Extract the recipes from the paginated result
        next_page=paginated_recipes['next_page'],
        prev_page=paginated_recipes['prev_page'],
        current_page=paginated_recipes['current_page'],
        total_pages=paginated_recipes['total_pages'],
        search_query=paginated_recipes['search_query'],
        articles=articles  # Pass the articles to the template
    )


@other_routes.route('/recipes1')
def recipes1():
    articles = get_topics_logic()
    keywords = ["6Months", "4to6Months", "9Months", "7Months"]
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes1.html')
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
    articles = get_topics_logic()
    keywords = ["9Months", "12Months", "10Months"]
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes2.html')
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
    articles = get_topics_logic()
    keywords = ["12Months", "forTheWholeFamily"]
    paginated_recipes = paginate_recipes(keywords=keywords, template_name='recipes3.html')
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
    return render_template('feeding_stages.html')


@other_routes.route('/signs')
def signs():
    return render_template('signs.html')


@other_routes.route('/search', methods=['POST'])
def search():
    search_term = request.form.get('search')
    logger = current_app.logger
    logger.info(f"Searching for recipes with query: {search_term}")

    if not search_term:
        flash("Please enter a search term.")
        return redirect(url_for('other_routes.recipes'))

    try:
        # Perform the search in the database
        recipes_query = Recipe.query.filter(
            Recipe.title.ilike(f"%{search_term}%") |
            Recipe.age_group.ilike(f"%{search_term}%")
        )

        # Pass the pre-filtered query to the paginate_recipes function
        pagination_data = paginate_recipes(recipes_query=recipes_query, template_name='search_results.html', search_query=search_term)

        # Render the template with pagination data
        return render_template('search_results.html', **pagination_data)

    except Exception as e:
        logger.error(f"Error processing the search: {e}", exc_info=True)
        flash("An error occurred while searching for recipes.")
        return redirect(url_for('other_routes.recipes'))



@other_routes.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    articles = get_topics_logic()
    logger = current_app.logger
    logger.info(f"Fetching details for meal ID: {meal_id}")

    try:
        # Fetch the recipe from the database using the default db.session
        meal_info = Recipe.query.get(meal_id)

        if not meal_info:
            logger.error(f"Meal ID {meal_id} not found in the database.")
            return render_template('404.html'), 404

        # Log the view (increment views and update last_viewed)
        meal_info.log_view()

        # Commit the transaction to save the changes
        db.session.commit()

        # Prepare meal information
        meal_info.image_url = meal_info.image_url or '/static/images/default-recipe.jpg'
        meal_info.method = meal_info.method or 'No instructions provided.'

        # Process the ingredients and instructions if they are JSON strings
        try:
            meal_info.ingredients = json.loads(meal_info.ingredients)
        except (json.JSONDecodeError, TypeError):
            meal_info.ingredients = []

        try:
            meal_info.method = json.loads(meal_info.method)
        except (json.JSONDecodeError, TypeError):
            meal_info.method = []

        # Successful retrieval
        logger.info(f"Successfully retrieved details for meal ID: {meal_id}")
        return render_template('meal_detail.html', meal=meal_info, articles=articles)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        db.session.rollback()  # Rollback in case of error
        return render_template('404.html'), 404


@other_routes.route('/favourite/<int:recipe_id>', methods=['POST'])
@login_required
def favourite_recipe(recipe_id):
    user_id = current_user.id

    # Check if the recipe is already in the user's favourites
    existing_favourite = db.session.query(Favourites).join(user_favourites).filter(
        user_favourites.c.user_id == user_id,
        user_favourites.c.favourite_id == Favourites.id,
        Favourites.recipe_id == recipe_id
    ).first()

    if existing_favourite is None:
        # If not, add the new favourite
        recipe_title = request.form['recipe_title']
        recipe_image = request.form['recipe_image']
        new_favourite = Favourites(recipe_id=recipe_id, recipe_title=recipe_title, recipe_image=recipe_image)
        db.session.add(new_favourite)
        db.session.commit()

        # Associate the favourite with the user
        current_user.favourites.append(new_favourite)
        db.session.commit()

        flash('Recipe added to favourites!', 'success')
    else:
        flash('Recipe already in favourites.', 'info')

    return redirect(url_for('other_routes.profile'))


@other_routes.route('/unfavourite/<int:recipe_id>', methods=['POST'])
@login_required
def unfavourite_recipe(recipe_id):
    user_id = current_user.id

    # Find the favourite recipe record
    favourite = db.session.query(Favourites).join(user_favourites).filter(
        user_favourites.c.user_id == user_id,
        user_favourites.c.favourite_id == Favourites.id,
        Favourites.recipe_id == recipe_id
    ).first()

    if favourite:
        # Remove the association between the user and the favourite recipe
        current_user.favourites.remove(favourite)
        db.session.commit()
        flash('Recipe removed from favourites!', 'success')
    else:
        flash('Recipe not found in favourites.', 'error')

    return redirect(url_for('other_routes.profile'))


@other_routes.route('/healthy_eating', methods=['GET', 'POST'])
def healthy_eating():
    articles = get_topics_logic()
    age_group = request.form.get('age_group')
    portion_sizes = []

    if age_group:
        portion_sizes = get_portion_sizes(age_group)

    return render_template('healthy_eating.html', portion_sizes=portion_sizes, age_group=age_group, articles=articles)

def get_portion_sizes(age_group):
    portions_api_key = '4f704df26c022d7001e8c639f94ed667'
    app_id = 'c51d8bff'
    headers = {
        'x-app-id': app_id,
        'x-app-key': portions_api_key,
        'Content-Type': 'application/json'
    }

    query = f'{age_group} food'
    endpoint = 'https://trackapi.nutritionix.com/v2/search/instant'
    params = {'query': query}

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)  # Debugging log

        # Assuming the response has a 'branded' or 'common' key with the relevant food items
        foods = data.get('branded', []) + data.get('common', [])
        portion_sizes = [{
            'food_name': food['food_name'],
            'serving_qty': food.get('serving_qty', 'N/A'),
            'serving_unit': food.get('serving_unit', 'N/A')
        } for food in foods]

        return portion_sizes
    except requests.exceptions.RequestException as e:
        print(f'Error fetching portion sizes: {e}')
        return []


@other_routes.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@other_routes.route('/proxy', methods=['GET'])
def proxy():
    age_group = request.args.get('age_group')
    print(f'Received age_group parameter: {age_group}')  # Debugging log

    # If no age_group is provided, return a 400 error
    if not age_group:
        return jsonify({'error': 'Missing age_group parameter'}), 400

    url = 'https://trackapi.nutritionix.com/v2/search/instant'
    headers = {
        'x-app-id': 'c51d8bff',
        'x-app-key': '4f704df26c022d7001e8c639f94ed667',
        'Content-Type': 'application/json'
    }
    params = {'query': age_group}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        print(f'Response content: {response.content}')
        return jsonify({'error': 'HTTP error occurred'}), 500
    except requests.exceptions.ConnectionError as conn_err:
        print(f'Connection error occurred: {conn_err}')
        return jsonify({'error': 'Connection error occurred'}), 500
    except requests.exceptions.Timeout as timeout_err:
        print(f'Timeout error occurred: {timeout_err}')
        return jsonify({'error': 'Request timed out'}), 500
    except requests.exceptions.RequestException as req_err:
        print(f'Request error occurred: {req_err}')
        return jsonify({'error': 'Request error occurred'}), 500
    except Exception as err:
        print(f'Other error occurred: {err}')
        return jsonify({'error': 'An error occurred'}), 500


@other_routes.route('/top-recipe')
def top_recipe():
    # Calculate the date for the previous day
    yesterday = datetime.now() - timedelta(days=1)
    start_of_yesterday = datetime.combine(yesterday, datetime.min.time())
    end_of_yesterday = datetime.combine(yesterday, datetime.max.time())

    # Get the most viewed recipe from the previous day
    top_recipe = Recipe.query.filter(Recipe.last_viewed >= start_of_yesterday,
                                     Recipe.last_viewed <= end_of_yesterday)\
                             .order_by(Recipe.views.desc())\
                             .first()

    return render_template('top_recipe.html', top_recipe=top_recipe)