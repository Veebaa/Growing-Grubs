import requests
from flask import Blueprint
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from spoonacular import API
from sqlalchemy.exc import SQLAlchemyError

from mod import logger, db
from models import Users, Favourites, user_favourites
from user_manager import RegistrationForm, LoginForm

other_routes = Blueprint("other_routes", __name__, static_folder='static', template_folder='../templates')

# Recipe API
api_key = 'c676336b8de04c04b131f2f91eb14b33'
spoonacular_api = API(api_key)
#  Health API
CDC_API_KEY = 'xbq22hetm32yj5rl2ogu4ewj'
CDC_API_SECRET = '5gmwqwzx1ke94m2i1wlx3e8hzvs4nnerfgekudxhao4g1x73lo'


@other_routes.route("/")
def index():
    articles = get_topics()
    return render_template("index.html", articles=articles)


@other_routes.route("/topics")
def get_topics():
    endpoint = ' https://data.cdc.gov/resource/wxz7-ekz9.json'
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in data:
            title = item.get('title', 'No Title')
            description = item.get('description', 'No Description')
            url = item.get('url', '#')
            articles.append({'title': title, 'description': description, 'url': url})

        if not articles:
            logger.info("No articles found from the API.")
        return jsonify(articles)

    except requests.RequestException as e:
        logger.error(f"Error fetching data from CDC API: {e}")
        return jsonify([]), 500


@other_routes.route('/register', methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()
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
    user_info = {
        'profile_image': current_user.profile_image,
        'username': current_user.username,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'email': current_user.email,
        'favourites': current_user.favourites
    }
    logger.info(f"User favourites: {user_info['favourites']}")
    return render_template('profile.html', user=user_info)


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


@other_routes.route('/recipes')
def recipes():
    return render_template('recipes.html')


@other_routes.route('/recipes1')
def recipes1():
    return render_template('recipes1.html')


@other_routes.route('/recipes2')
def recipes2():
    return render_template('recipes2.html')


@other_routes.route('/recipes3')
def recipes3():
    return render_template('recipes3.html')


@other_routes.route('/feeding_stages')
def feeding_stages():
    return render_template('feeding_stages.html')


@other_routes.route('/signs')
def signs():
    return render_template('signs.html')


@other_routes.route('/search', methods=['POST'])
def search():
    search_term = request.form.get('search')
    logger.info(f"Searching for meals with query: {search_term}")

    if not search_term:
        flash("Please enter a search term.")
        return redirect(url_for('other_routes.recipes'))

    try:
        # Querying the Spoonacular API for complex search
        endpoint = f'https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&query={search_term}'
        response = requests.get(endpoint)
        results = response.json()
        logger.info(f"Search results: {results}")

        if not results or 'results' not in results:
            flash("Invalid response from the API.")
            return redirect(url_for('other_routes.recipes'))

        meals = results.get('results', [])

        if meals:  # Check if meals were returned
            return render_template('recipes.html', meals=meals, search_query=search_term)
        else:
            flash("No meals found matching your search term.")

    except Exception as e:
        logger.error(f"Error fetching data from Spoonacular: {e}")
        flash("Error fetching data from Spoonacular: " + str(e))

    return redirect(url_for('other_routes.recipes'))


@other_routes.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    logger.info(f"Fetching details for meal ID: {meal_id}")

    try:
        response = requests.get(f'https://api.spoonacular.com/recipes/{meal_id}/information?apiKey=c676336b8de04c04b131f2f91eb14b33')
        meal_info = response.json()  # Converts the response to JSON
        logger.info(f"Meal info: {meal_info}")  # Logs the meal structure

        if not meal_info or 'error' in meal_info:
            logger.error("Invalid meal info received or Meal ID not found.")
            return render_template('404.html'), 404  # Serve 404 page

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return render_template('404.html'), 404  # Serve 404 page

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return render_template('404.html'), 404  # Serve 404 page

    meal_info['id'] = meal_id
    meal_info['image'] = meal_info.get('image', '/static/images/default-recipe.jpg')
    meal_info['instructions'] = meal_info.get('instructions', 'No instructions provided.')
    meal_info['extendedIngredients'] = meal_info.get('extendedIngredients', [])
    meal_info['preparationMinutes'] = meal_info.get('preparationMinutes', 'N/A')
    meal_info['cookingMinutes'] = meal_info.get('cookingMinutes', 'N/A')
    meal_info['readyInMinutes'] = meal_info.get('readyInMinutes', 'N/A')

    # Successful retrieval
    logger.info(f"Successfully retrieved details for meal ID: {meal_id}")

    return render_template('meal_detail.html', meal=meal_info)


# app.py

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


@other_routes.route('/nutrition_widget/<int:meal_id>')
def nutrition_widget(meal_id):
    logger.info(f"Generating nutrition widget for meal ID: {meal_id}")

    try:
        # Fetching meal information
        response = spoonacular_api.get_recipe_information(meal_id)
        meal_info = response.json()

        if not meal_info or 'error' in meal_info:
            logger.error("Invalid meal info received or Meal ID not found.")
            return "Error: Meal information not found.", 404

        # Preparing ingredient list for the widget
        ingredients = "\n".join([ingredient['original'] for ingredient in meal_info['extendedIngredients']])
        servings = meal_info.get('servings', 1)
        api_key = 'c676336b8de04c04b131f2f91eb14b33'

        # Preparing POST data for the widget
        post_data = {
            'defaultCss': True,
            'ingredientList': ingredients,
            'servings': servings
        }

        # Calling Spoonacular API to get the widget HTML
        widget_response = requests.post(
            f'https://api.spoonacular.com/recipes/visualizeNutrition?apiKey={api_key}',
            data=post_data
        )
        widget_html = widget_response.text

        return widget_html

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return "Error: Unable to generate widget.", 500
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return "Error: Unable to generate widget.", 500


@other_routes.route('/healthy_eating')
def healthy_eating():
    baby_tips = get_health_tips('baby')
    toddler_tips = get_health_tips('toddler')
    family_tips = get_health_tips('family')

    return render_template('healthy_eating.html', baby_tips=baby_tips, toddler_tips=toddler_tips,
                           family_tips=family_tips)


def get_health_tips(category):
    api_key: str = 'c676336b8de04c04b131f2f91eb14b33'
    endpoint = f'https://api.spoonacular.com/food/search?apiKey={api_key}&query={category}&number=10'
    response = requests.get(endpoint)
    if response.status_code == 200:
        data = response.json()
        return data['searchResults']
    else:
        return []


@other_routes.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

