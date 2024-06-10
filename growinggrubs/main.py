import os
import json

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from database import db, User

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET'])
def register_user():
    return render_template("register_user.html")


if __name__ == "__main__":
    app.run(debug=True)
