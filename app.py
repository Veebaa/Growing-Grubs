import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import logging
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError, Email, Regexp
from spoonacular import API
from flask_migrate import Migrate
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
app.logger.addHandler(console_handler)

# adding configuration for using sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SECRET_KEY'] = 'secret_key'
app.config['WTF_CSRF_SECRET_KEY'] = 'your_csrf_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)  # Initialize the SQLAlchemy instance with the Flask app
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.init_app(app)

# Recipe API
api_key = 'c676336b8de04c04b131f2f91eb14b33'
spoonacular_api = API(api_key)

#  Health API
CDC_API_KEY = 'xbq22hetm32yj5rl2ogu4ewj'
CDC_API_SECRET = '5gmwqwzx1ke94m2i1wlx3e8hzvs4nnerfgekudxhao4g1x73lo'


# forms_fields.py


class RegistrationForm(FlaskForm):
    """ Registration form"""

    username = StringField('username',
                           validators=[InputRequired(message="Username required"),
                                       Length(min=4, max=25, message="Username must be between 4 and 25 characters"),
                                       Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only letters, numbers, dots, or underscores', )])
    first_name = StringField('firstname',
                             validators=[InputRequired(message="First name required"),
                                         Length(min=1, max=25,
                                                message="First name must be between 1 and 25 characters")])
    last_name = StringField('lastname',
                            validators=[InputRequired(message="Last name required"),
                                        Length(min=1, max=25, message="Last name must be between 1 and 25 characters")])
    email = StringField('email',
                        validators=[InputRequired(message="Email required"), Email()])
    password = PasswordField('password',
                             validators=[InputRequired(message="Password required"),
                                         EqualTo('confirm_password', message='Passwords do not match.')])
    confirm_password = PasswordField('confirm_password',
                                     validators=[InputRequired(message="Password required"), ])
    profile_image = SelectField('Profile Image', choices=[
        ('avo.jpg', 'Avocado'),
        ('cherries.jpg', 'Cherries'),
        ('orange.jpg', 'Orange'),
        ('strawberry.jpg', 'Strawberry'),
        ('watermelon.jpg', 'Watermelon'),
    ], validators=[InputRequired(message="Please select a profile image")])
    submit = SubmitField('Register')

    def validate_email(self, field):
        """ Email in db checker"""
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """ Username in db checker"""
        if Users.query.filter_by(username=field.data).first():
            raise ValidationError('Sorry! Username already in use.')


def invalid_credentials(form, field):
    """ Username and password checker """

    password = field.data
    username = form.username.data

    # Check username is invalid
    user_data = Users.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Username or password is incorrect")

    # Check password in invalid
    elif not user_data.check_password(password):
        raise ValidationError("Username or password is incorrect")


class LoginForm(FlaskForm):
    """ Login form """

    username = StringField('username', validators=[InputRequired(message="Username required")])
    password = PasswordField('password', validators=[InputRequired(message="Password required"), invalid_credentials])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# models.py

# Association table for the many-to-many relationship
user_favourites = db.Table('user_favourites',
                           db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                           db.Column('favourite_id', db.Integer, db.ForeignKey('favourites.id'), primary_key=True)
                           )


class Users(UserMixin, db.Model):
    """ Table for users """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_image = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Relationship to Favourites
    favourites = db.relationship('Favourites', secondary=user_favourites, backref=db.backref('users', lazy='dynamic'))


class Favourites(db.Model):
    __tablename__ = 'favourites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    recipe_title = db.Column(db.String(200), nullable=False)
    recipe_image = db.Column(db.String(200), nullable=False)

# app.py


def yesno(value, yes='Yes', no='No'):
    return yes if value else no


app.jinja_env.filters['yesno'] = yesno


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/topics")
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
            app.logger.info("No articles found from the API.")
        return jsonify(articles)

    except requests.RequestException as e:
        app.logger.error(f"Error fetching data from CDC API: {e}")
        return jsonify([]), 500


@app.route("/")
def index():
    articles = get_topics()
    return render_template("index.html", articles=articles)


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        app.logger.info(f"Registering new User {form.username.data}")
        try:
            user = Users(username=form.username.data, first_name=form.first_name.data,
                         last_name=form.last_name.data, email=form.email.data, profile_image=form.profile_image.data)
            user.set_password(form.password.data)  # Hash the password
            db.session.add(user)
            db.session.commit()

            app.logger.info(f"User {form.username.data} registered successfully!")
            return redirect(url_for('login'))

        except SQLAlchemyError as e:
            app.logger.error("Registration failed!")
            db.session.rollback()
            return f"Commit failed. Error: {e}"

    return render_template('register_user.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        app.logger.info(f'User {current_user.username} is authenticated. Redirecting to profile page.')
        return redirect(url_for('profile'))

    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')  # Flash the error message
            return redirect(url_for('login'))  # Redirect back to login

        login_user(user, remember=form.remember.data)
        app.logger.info(f'User {user.username} logged in successfully.')

        next_page = request.args.get('next')  # Get the 'next' parameter
        if next_page:  # User tried to access a protected route
            return redirect(next_page)
        else:
            app.logger.info(f'Redirecting user {user.username} to profile page.')
            return redirect(next_page) if next_page else redirect(url_for('profile'))  # Redirect to profile page

    return render_template('login.html', title='Log In', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('index'))


@app.route('/profile')
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
    app.logger.info(f"User favourites: {user_info['favourites']}")
    return render_template('profile.html', user=user_info)


@app.route('/edit_profile', methods=['POST'])
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

    return redirect(url_for('profile'))


@app.route('/recipes')
def recipes():
    return render_template('recipes.html')


@app.route('/recipes1')
def recipes1():
    return render_template('recipes1.html')


@app.route('/recipes2')
def recipes2():
    return render_template('recipes2.html')


@app.route('/recipes3')
def recipes3():
    return render_template('recipes3.html')


@app.route('/feeding_stages')
def feeding_stages():
    return render_template('feeding_stages.html')


@app.route('/signs')
def signs():
    return render_template('signs.html')


@app.route('/search', methods=['POST'])
def search():
    search_term = request.form.get('search')
    app.logger.info(f"Searching for meals with query: {search_term}")

    if not search_term:
        flash("Please enter a search term.")
        return redirect(url_for('recipes'))

    try:
        # Querying the Spoonacular API for complex search
        endpoint = f'https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&query={search_term}'
        response = requests.get(endpoint)
        results = response.json()
        app.logger.info(f"Search results: {results}")

        if not results or 'results' not in results:
            flash("Invalid response from the API.")
            return redirect(url_for('recipes'))

        meals = results.get('results', [])

        if meals:  # Check if meals were returned
            return render_template('recipes.html', meals=meals, search_query=search_term)
        else:
            flash("No meals found matching your search term.")

    except Exception as e:
        app.logger.error(f"Error fetching data from Spoonacular: {e}")
        flash("Error fetching data from Spoonacular: " + str(e))

    return redirect(url_for('recipes'))


@app.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    app.logger.info(f"Fetching details for meal ID: {meal_id}")

    try:
        response = requests.get(f'https://api.spoonacular.com/recipes/{meal_id}/information?apiKey=c676336b8de04c04b131f2f91eb14b33')
        meal_info = response.json()  # Converts the response to JSON
        app.logger.info(f"Meal info: {meal_info}")  # Logs the meal structure

        if not meal_info or 'error' in meal_info:
            app.logger.error("Invalid meal info received or Meal ID not found.")
            return render_template('404.html'), 404  # Serve 404 page

    except requests.HTTPError as http_err:
        app.logger.error(f"HTTP error occurred: {http_err}")
        return render_template('404.html'), 404  # Serve 404 page

    except Exception as e:
        app.logger.error(f"Unexpected error occurred: {e}")
        return render_template('404.html'), 404  # Serve 404 page

    meal_info['id'] = meal_id
    meal_info['image'] = meal_info.get('image', '/static/images/default-recipe.jpg')
    meal_info['instructions'] = meal_info.get('instructions', 'No instructions provided.')
    meal_info['extendedIngredients'] = meal_info.get('extendedIngredients', [])
    meal_info['preparationMinutes'] = meal_info.get('preparationMinutes', 'N/A')
    meal_info['cookingMinutes'] = meal_info.get('cookingMinutes', 'N/A')
    meal_info['readyInMinutes'] = meal_info.get('readyInMinutes', 'N/A')

    # Successful retrieval
    app.logger.info(f"Successfully retrieved details for meal ID: {meal_id}")

    return render_template('meal_detail.html', meal=meal_info)


# app.py

@app.route('/favourite/<int:recipe_id>', methods=['POST'])
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

    return redirect(url_for('profile'))


@app.route('/nutrition_widget/<int:meal_id>')
def nutrition_widget(meal_id):
    app.logger.info(f"Generating nutrition widget for meal ID: {meal_id}")

    try:
        # Fetching meal information
        response = spoonacular_api.get_recipe_information(meal_id)
        meal_info = response.json()

        if not meal_info or 'error' in meal_info:
            app.logger.error("Invalid meal info received or Meal ID not found.")
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
        app.logger.error(f"HTTP error occurred: {http_err}")
        return "Error: Unable to generate widget.", 500
    except Exception as e:
        app.logger.error(f"Unexpected error occurred: {e}")
        return "Error: Unable to generate widget.", 500


@app.route('/healthy_eating')
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


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
