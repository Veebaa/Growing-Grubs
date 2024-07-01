import os
import json
import sqlalchemy

from flask import Flask, render_template, request, redirect, url_for, send_from_directory


from database import db, User

app = Flask(__name__)


basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "growinggrubs.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET'])
def register_user():
    return render_template("register_user.html")


if __name__ == "__main__":
    app.run(debug=True)
