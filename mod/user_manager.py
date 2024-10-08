from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, DataRequired

# Create a LoginManager instance to manage user sessions
login_manager = LoginManager()


def init_login_manager(app):
    """Initialize the LoginManager with the Flask app."""
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Callback function to load a user given the user_id."""
    from mod.models import Users  # Local import to avoid circular dependency
    return Users.query.get(int(user_id))  # Retrieve user from the database using user_id


class RegistrationForm(FlaskForm):
    """Form for user registration."""
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

    def validate_email(self, field):
        """Check if the email is already registered in the database."""
        from mod.models import Users  # Local import
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """Check if the username is already taken in the database."""
        from mod.models import Users  # Local import
        if Users.query.filter_by(username=field.data).first():
            raise ValidationError('Sorry! Username already in use.')


def invalid_credentials(form, field):
    """Custom validator for checking invalid username and password."""
    password = field.data
    username = form.username.data

    from mod.models import Users  # Local import
    user_data = Users.query.filter_by(username=username).first()
    if user_data is None or not user_data.check_password(password):
        raise ValidationError("Username or password is incorrect")


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('username', validators=[InputRequired(message="Username required")])
    password = PasswordField('password', validators=[InputRequired(message="Password required"), invalid_credentials])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class DayMealForm(FlaskForm):
    breakfast = SelectField('Breakfast', coerce=int)
    lunch = SelectField('Lunch', coerce=int)
    dinner = SelectField('Dinner', coerce=int)


class MealPlanForm(FlaskForm):
    name = StringField('Meal Plan Name', validators=[DataRequired()])
    monday = FormField(DayMealForm)
    tuesday = FormField(DayMealForm)
    wednesday = FormField(DayMealForm)
    thursday = FormField(DayMealForm)
    friday = FormField(DayMealForm)
    saturday = FormField(DayMealForm)
    sunday = FormField(DayMealForm)
    submit = SubmitField('Create Meal Plan')
