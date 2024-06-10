from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)
    email = db.Column(String(100), nullable=False)
    password = db.Column(String(100), nullable=False)

    def __str__(self):
        return self.name


# class Todo(db.Model):
#     id = db.Column(Integer, primary_key=True)
#     name = db.Column(String(100), nullable=False)
#     recommendations = []
#     recommendations_json = db.Column(db.JSON)
#
#     def __str__(self):
#         return self.name

