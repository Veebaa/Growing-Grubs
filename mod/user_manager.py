from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, Regexp, Email, EqualTo, ValidationError
from mod.models import Users

# Create a LoginManager instance to manage user sessions
login_manager = LoginManager()


def init_login_manager(app):
    """Initialize the LoginManager with the Flask app."""
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Callback function to load a user given the user_id."""
    return Users.query.get(int(user_id))  # Retrieve user from the database using user_id


class RegistrationForm(FlaskForm):
    """Form for user registration."""

    username = StringField('username',
                           validators=[InputRequired(message="Username required"),  # Ensure username is provided
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
    ], validators=[InputRequired(message="Please select a profile image")])  # Ensure profile image is selected
    submit = SubmitField('Register')  # Submit button for the form

    def validate_email(self, field):
        """Check if the email is already registered in the database."""
        if Users.query.filter_by(email=field.data).first():  # Query for existing email
            raise ValidationError('Email already registered.')  # Raise error if email is found

    def validate_username(self, field):
        """Check if the username is already taken in the database."""
        if Users.query.filter_by(username=field.data).first():  # Query for existing username
            raise ValidationError('Sorry! Username already in use.')  # Raise error if username is found


def invalid_credentials(form, field):
    """Custom validator for checking invalid username and password."""
    password = field.data  # Get the entered password
    username = form.username.data  # Get the entered username

    # Check if the username exists in the database
    user_data = Users.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Username or password is incorrect")  # Raise error if username is not found

    # Check if the password matches the stored password
    elif not user_data.check_password(password):
        raise ValidationError("Username or password is incorrect")  # Raise error if password is incorrect


class LoginForm(FlaskForm):
    """Form for user login."""
    # Ensure username is provided
    username = StringField('username', validators=[InputRequired(message="Username required")])
    # Ensure password is provided and validate credentials
    password = PasswordField('password', validators=[InputRequired(message="Password required"),
                                                     invalid_credentials])
    # Checkbox for remembering user login
    remember = BooleanField('Remember Me')
    # Submit button for the form
    submit = SubmitField('Login')
