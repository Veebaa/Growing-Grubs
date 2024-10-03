import json
import os
import requests
import logging
import random
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from mod import db
from mod.models import Users, Favourites, user_favourites, Recipe, MealPlan, MealPlanDay
from mod.user_manager import RegistrationForm, LoginForm, MealPlanForm
from datetime import datetime, timedelta
from dotenv import load_dotenv

other_routes = Blueprint("other_routes", __name__, static_folder='static', template_folder='../templates')

load_dotenv()

if logging.getLogger('growing_grubs_logger') is None:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('growing_grubs_logger')


@other_routes.errorhandler(404)
def not_found_error(e):
    current_app.logger.error(f"404 error: {e}")
    # Render a 404 error page if a route is not found
    return render_template('404.html'), 404


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
    api_key = os.getenv('NHS_API_KEY')
    endpoint = 'https://api.nhs.uk/conditions'
    headers = {
        'subscription-key': api_key,
        'Content-Type': 'application/json'
    }
    logger = current_app.logger
    try:
        response = requests.get(endpoint, headers=headers, params={'topic': 'children development, childhood illness'})
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data.get('significantLink', []):
            name = item.get('name', 'No Title')
            description = item.get('description', 'No Description')
            url = item.get('url', '#')
            articles.append({'name': name, 'description': description, 'url': url})

        if len(articles) >= 2:
            logger.info(articles)  # Log random articles
            return random.sample(articles, 2)
        else:
            return articles

    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching data from NHS API: {e}")
        return []


@other_routes.route('/site_map')
def sitemap():
    return render_template("site_map.html")


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

            flash('You have been successfully registered.', 'success')

            logger.info(f"User {form.username.data} registered successfully!")
            # Redirect the user to the login page after successful registration
            return redirect(url_for('other_routes.login'))

        except SQLAlchemyError as e:
            # Log an error if the registration fails and roll back the session
            logger.error(f"IntegrityError during registration: {e}")
            db.session.rollback()
            flash('A database error occurred. Please try again.', 'error')
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
        logger.info("Login form validated successfully")

        # Retrieve the user by username
        user = Users.query.filter_by(username=form.username.data).first()
        logger.info(f"Attempting login for username: {form.username.data}")

        # Log whether the user was found and whether the password matches
        logger.info(f"User found: {user is not None}")
        if user:
            logger.info(f"Password correct: {user.check_password(form.password.data)}")
        else:
            logger.info("User not found")

        # Check if the user exists and if the password is correct
        if user is None or not user.check_password(form.password.data):
            # Log the error if login fails
            logger.info(f"Login failed for user {form.username.data}")
            logger.info(f"Provided password: {form.password.data}")
            if user:
                logger.info(f"Hashed password: {user.password}")

            # Flash an error message if the login fails
            flash('Invalid login credentials.', 'error')
            return redirect(url_for('other_routes.login'))

        # Log the user in and remember their session based on the form input
        login_user(user, remember=form.remember.data)
        logger.info(f'User {user.username} logged in successfully.')

        # Redirect to the 'next' parameter
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
    flash('You have been logged out.', 'success')
    # Redirect the user to the index page
    return redirect(url_for('other_routes.index'))


@other_routes.route('/profile', methods=['GET', 'POST'])
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

    # Fetch the user's existing meal plan to render
    meal_plans = MealPlan.query.filter_by(user_id=current_user.id).all()
    logger.info(f'Fetched {len(meal_plans)} meal plans for user ID {current_user.id}.')

    return render_template('profile.html', user=user_info, available_profile_images=available_profile_images, meal_plans=meal_plans)


@other_routes.route('/meal-planner', methods=['GET', 'POST'])
@login_required
def meal_planner():
    logger = current_app.logger

    form = MealPlanForm()
    favourites = [(favourite.recipe_id, favourite.recipe.title) for favourite in current_user.favourites]

    # Set meal choices for the form
    for day_form in [form.monday, form.tuesday, form.wednesday, form.thursday, form.friday, form.saturday, form.sunday]:
        day_form.breakfast.choices = favourites
        day_form.lunch.choices = favourites
        day_form.dinner.choices = favourites

    if form.validate_on_submit():
        # Meal plan creation logic
        meal_plan = MealPlan(name=form.name.data, user=current_user)
        db.session.add(meal_plan)
        db.session.flush()

        for day_name, day_form in [('Monday', form.monday), ('Tuesday', form.tuesday), ('Wednesday', form.wednesday),
                                   ('Thursday', form.thursday), ('Friday', form.friday), ('Saturday', form.saturday),
                                   ('Sunday', form.sunday)]:
            meal_plan_day = MealPlanDay(
                day=day_name,
                meal_plan_id=meal_plan.id,
                breakfast_id=day_form.breakfast.data,
                lunch_id=day_form.lunch.data,
                dinner_id=day_form.dinner.data
            )
            db.session.add(meal_plan_day)

        db.session.commit()
        flash('Meal plan created successfully!')
        return redirect(url_for('other_routes.meal_planner', meal_plan_id=meal_plan.id))

    return render_template('meal_planner.html', form=form)


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
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        # Roll back the session and flash an error message if the update fails
        db.session.rollback()
        flash('Error updating profile: ' + str(e), 'error')

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
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
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

        # Convert recipes to dictionary for easier rendering in templates
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


@other_routes.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    articles = get_topics_logic()  # Fetch articles logic

    logger = current_app.logger
    logger.info(f"Fetching details for meal ID: {meal_id}")

    try:
        with db.session.no_autoflush:
            meal_info = db.session.get(Recipe, meal_id)

            if not meal_info:
                logger.error(f"Meal ID {meal_id} not found in the database.")
                return render_template('404.html'), 404

            # Log the view count
            meal_info.log_view()

            # Check if 'no_flush' parameter is set in the request arguments
            no_flush = request.args.get('no_flush') == 'true'

            if not no_flush:
                db.session.commit()
            else:
                db.session.flush()

            # Default image and method handling
            meal_info.image_url = meal_info.image_url or '/static/images/comingsoon.jpg'
            meal_info.method = meal_info.method or 'No instructions provided.'

            logger.info(f"Raw ingredients data: {meal_info.ingredients}")

            # Parsing ingredients and method
            try:
                meal_info.ingredients = json.loads(meal_info.ingredients) if isinstance(meal_info.ingredients,
                                                                                        str) else []
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error for ingredients: {e}")
                meal_info.ingredients = []  # Fallback to an empty list or handle accordingly

            try:
                meal_info.method = json.loads(meal_info.method) if isinstance(meal_info.method, str) else []
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error for method: {e}")
                meal_info.method = []  # Fallback to an empty list or handle accordingly

            logger.info(f"Successfully retrieved details for meal ID: {meal_id}")
            return render_template('meal_detail.html', meal=meal_info, articles=articles)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        db.session.rollback()
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
        return jsonify({'success': True, 'recipe_id': recipe_id, 'message': 'Recipe removed from favourites!'})
    else:
        return jsonify({'success': False, 'message': 'Recipe not found in favourites.'})


@other_routes.route('/meal-plan/<int:meal_plan_id>')
@login_required
def view_meal_plan(meal_plan_id):
    logger = current_app.logger  # Initialize the logger

    meal_plan = MealPlan.query.get_or_404(meal_plan_id)

    if meal_plan.user != current_user:
        flash('You do not have permission to view this meal plan.')
        return redirect(url_for('index'))

    logger.info(f"User {current_user.username} is viewing meal plan: {meal_plan.name}")

    # Fetch meal plan details for JSON response
    meal_plan_days = MealPlanDay.query.filter_by(meal_plan_id=meal_plan.id).all()
    days = [
        {
            'day': meal_plan_day.day,
            'breakfast': meal_plan_day.breakfast.title,
            'lunch': meal_plan_day.lunch.title,
            'dinner': meal_plan_day.dinner.title
        }
        for meal_plan_day in meal_plan_days
    ]

    logger.info(f"Meal plan details for {meal_plan.name}: {days}")

    return jsonify({'name': meal_plan.name, 'days': days})


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
        flash('Please enter a search term.', 'error')
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
        flash('An error occurred while searching for recipes.', 'error')
        return redirect(url_for('other_routes.recipes'))


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


def get_portion_sizes(age_group, offset=0, limit=5):
    portions_api_key = '4f704df26c022d7001e8c639f94ed667'
    app_id = 'c51d8bff'
    headers = {
        'x-app-id': app_id,
        'x-app-key': portions_api_key,
        'Content-Type': 'application/json'
    }

    query = f'{age_group} food'
    endpoint = 'https://trackapi.nutritionix.com/v2/search/instant'
    params = {
        'query': query
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)  # Debugging log to check the API response

        foods = data.get('branded', []) + data.get('common', [])
        portion_sizes = [{
            'food_name': food['food_name'],
            'serving_qty': food.get('serving_qty', 'N/A'),
            'serving_unit': food.get('serving_unit', 'N/A')
        } for food in foods]

        # Simulate pagination if possible (if you get all items and handle pagination manually)
        paginated_items = portion_sizes[offset:offset + limit]

        return {
            'portion_sizes': paginated_items,
            'total_items': len(portion_sizes)  # Provide total number of items for pagination controls
        }
    except requests.exceptions.RequestException as e:
        print(f'Error fetching portion sizes: {e}')
        return {'portion_sizes': [], 'total_items': 0}


@other_routes.route('/proxy', methods=['GET'])
def proxy():
    age_group = request.args.get('age_group')  # Get the age group from query parameters
    offset = int(request.args.get('offset', 0))  # Get the offset parameter, default to 0
    limit = int(request.args.get('limit', 5))  # Get the limit parameter, default to 5

    # If no age_group is provided, return a 400 error
    if not age_group:
        return jsonify({'error': 'Missing age_group parameter'}), 400

    url = 'https://trackapi.nutritionix.com/v2/search/instant'  # Nutritionix API endpoint
    headers = {
        'x-app-id': os.getenv('NUTRITIONIX_APP_ID'),   # Use environment variables for sensitive info
        'x-app-key': os.getenv('NUTRITIONIX_API_KEY'),   # Use environment variables for sensitive info
        'Content-Type': 'application/json'
    }
    params = {'query': age_group}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)  # Make the API request
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Parse the response JSON

        # Extract food items from the response
        foods = data.get('branded', []) + data.get('common', [])
        paginated_items = foods[offset:offset + limit]

        # Debugging print statements
        print(f"Response Data: {data}")
        print(f"Paginated Items: {paginated_items}")

        return jsonify({
            'portion_sizes': paginated_items,
            'total_items': len(foods)  # Provide total number of items for pagination controls
        })
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Log HTTP errors
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
