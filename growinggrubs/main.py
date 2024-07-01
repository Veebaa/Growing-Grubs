import os
import json
import sqlalchemy
from sqlalchemy import Integer, String, create_engine, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

#from database import Users

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "growinggrubs.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# db.init_app(app)
#
# with app.app_context():
#     db.create_all()


class Users(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')

        new_user = Users(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        print('User registered successfully!')

        users = Users.query.all()
        for user in users:
            print(user)

        return redirect(url_for('index'))  # Redirect to the home page

    else:
        return render_template('register_user.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
