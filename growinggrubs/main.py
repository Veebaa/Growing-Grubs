import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Column
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError, Email, Regexp
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///site.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)  # Initialize the SQLAlchemy instance with the Flask app

login_manager = LoginManager(app)
login_manager.init_app(app)


# forms_fields.py

def invalid_credentials(form, field):
    """ Username and password checker """

    password = field.data
    username = form.username.data

    # Check username is invalid
    user_data = Users.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Username or password is incorrect")

    # Check password in invalid
    elif not pbkdf2_sha256.verify(password, user_data.hashed_pswd):
        raise ValidationError("Username or password is incorrect")


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
    submit = SubmitField('Register')

    def validate_email(self, field):
        """ Email in db checker"""
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """ Username in db checker"""
        if Users.query.filter_by(username=field.data).first():
            raise ValidationError('Sorry! Username already in use.')


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
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Recipes(db.Model):
    """ Table for recipes """
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    ingredients = Column(String(255), nullable=False)
    instructions = Column(String(255), nullable=False)


# main.py


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.before_request
def before_request():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        user = Users(username=username, first_name=first_name, last_name=last_name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        flash('User registered successfully!')

        return redirect(url_for('login'))
    return render_template('register_user.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('profile'))
    return render_template('login.html', title='Log In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


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


if __name__ == "__main__":
    app.run(debug=True)
