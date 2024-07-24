import os
from flask import Flask, render_template, request, redirect, url_for, flash
import logging
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError, Email, Regexp
from passlib.hash import pbkdf2_sha256
from spoonacular import API
from flask_migrate import Migrate

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO)

# adding configuration for using a sqlite database
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


# app.py


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


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

        next_page = request.args.get('next')   # Get the 'next' parameter
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
        'email': current_user.email
    }
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


@app.route('/healthy_eating')
def healthy_eating():
    return render_template('healthy_eating.html')


@app.route('/search', methods=['POST'])
def search():
    search_term = request.form.get('search')
    app.logger.info(f"Searching for meals with query: {search_term}")

    if not search_term:
        flash("Please enter a search term.")
        return redirect(url_for('recipes'))

    try:
        # This uses the API endpoint that allows searching for both recipe names and ingredients
        results = spoonacular_api.get_recipes_complex_search(query=search_term)
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
        meal_info = spoonacular_api.get_recipe_information(meal_id)
        app.logger.info(f"Meal information fetched successfully: {meal_info}")
        if meal_info is None:
            flash("Invalid meal information received.")
            return redirect(url_for('recipes'))
    except Exception as e:
        app.logger.error(f"Error fetching meal details: {e}")
        flash(f"Error fetching meal details: {e}")
        return redirect(url_for('recipes'))

    return render_template('meal_detail.html', meal=meal_info)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
