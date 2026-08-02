"""User management, authentication, and form handling for Growing Grubs."""

from typing import Optional
from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, DataRequired
from flask import Flask

# Create a LoginManager instance to manage user sessions
login_manager = LoginManager()


def init_login_manager(app: Flask) -> None:
    """
    Initialize the LoginManager with the Flask app.
    
    Args:
        app: Flask application instance
    """
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str) -> Optional['Users']:
    """
    Callback function to load a user given the user_id.
    
    This function is called by Flask-Login to load the current user
    from the database for each request.
    
    Args:
        user_id: The ID of the user to load
    
    Returns:
        Users: The user object, or None if not found
    """
    from mod.models import Users  # Local import to avoid circular dependency
    return Users.query.get(int(user_id))


class RegistrationForm(FlaskForm):
    """
    Form for user registration.
    
    Validates username, email, password, and profile image selection.
    Includes custom validators to check for existing emails and usernames.
    """
    username = StringField('username',
                           validators=[InputRequired(message="Username required"),
                                       Length(min=4, max=25, message="Username must be between 4 and 25 characters")])
    first_name = StringField('firstname',
                             validators=[InputRequired(message="First name required"),
                                         Length(min=1, max=25, message="First name must be between 1 and 25 characters")])
    last_name = StringField('lastname',
                            validators=[InputRequired(message="Last name required"),
                                        Length(min=1, max=25, message="Last name must be between 1 and 25 characters")])
    email = StringField('email',
                        validators=[InputRequired(message="Email required"),
                                    Email()])
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

    def validate_email(self, field) -> None:
        """
        Validate that the email is not already registered.
        
        Args:
            field: The email field being validated
            
        Raises:
            ValidationError: If the email is already registered
        """
        from mod.models import Users  # Local import
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field) -> None:
        """
        Validate that the username is not already taken.
        
        Args:
            field: The username field being validated
            
        Raises:
            ValidationError: If the username is already in use
        """
        from mod.models import Users  # Local import
        if Users.query.filter_by(username=field.data).first():
            raise ValidationError('Sorry! Username already in use.')


def invalid_credentials(form: FlaskForm, field) -> None:
    """
    Custom validator for checking invalid username and password combinations.
    
    Args:
        form: The form being validated
        field: The password field being validated
        
    Raises:
        ValidationError: If the username/password combination is incorrect
    """
    password = field.data
    username = form.username.data

    from mod.models import Users  # Local import
    user_data = Users.query.filter_by(username=username).first()
    if user_data is None or not user_data.check_password(password):
        raise ValidationError("Username or password is incorrect")


class LoginForm(FlaskForm):
    """
    Form for user login.
    
    Validates username and password using the custom invalid_credentials validator.
    Includes a "Remember Me" checkbox for persistent login sessions.
    """
    username = StringField('username', validators=[InputRequired(message="Username required")])
    password = PasswordField('password', validators=[InputRequired(message="Password required"), invalid_credentials])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class DayMealForm(FlaskForm):
    """
    Form for selecting meals for a single day.
    
    Used as a nested form within MealPlanForm to allow meal selection
    for breakfast, lunch, and dinner.
    """
    breakfast = SelectField('Breakfast', coerce=int)
    lunch = SelectField('Lunch', coerce=int)
    dinner = SelectField('Dinner', coerce=int)


class MealPlanForm(FlaskForm):
    """
    Form for creating a complete weekly meal plan.
    
    Contains nested DayMealForm instances for each day of the week,
    allowing users to select recipes for each meal and day.
    """
    name = StringField('Meal Plan Name', validators=[DataRequired()])
    monday = FormField(DayMealForm)
    tuesday = FormField(DayMealForm)
    wednesday = FormField(DayMealForm)
    thursday = FormField(DayMealForm)
    friday = FormField(DayMealForm)
    saturday = FormField(DayMealForm)
    sunday = FormField(DayMealForm)
    submit = SubmitField('Create Meal Plan')
