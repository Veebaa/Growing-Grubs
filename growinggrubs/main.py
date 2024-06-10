import os
import json

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from database import db, User

app = Flask(__name__, static_folder='../templates')


@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    app.run(debug=True)
