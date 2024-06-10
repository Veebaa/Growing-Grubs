import os
import json

from flask import Flask, render_template, request, redirect, url_for, g

from database import db, Todo

app = Flask(__name__)

