import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from forms_fields import RegistrationForm, LoginForm
from models import Users

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///site.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)  # Initialize the SQLAlchemy instance with the Flask app

login_manager = LoginManager(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# @app.before_request
# def before_request():
#     db.create_all()


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
