"""Database models for the Growing Grubs application."""

import json
from typing import Optional, Dict, Any, List

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from mod import db
from datetime import datetime

# Association table for the many-to-many relationship
user_favourites = db.Table('user_favourites',
                           db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                           db.Column('favourite_id', db.Integer, db.ForeignKey('favourites.id'), primary_key=True),
                           extend_existing=True
                           )


class Users(UserMixin, db.Model):
    """ Table for users """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_image = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user's password."""
        return check_password_hash(self.password, password)

    # Relationship to Favourites
    favourites = db.relationship('Favourites', secondary=user_favourites, backref=db.backref('users', lazy='dynamic'))


class Favourites(db.Model):
    """ Table for Favourites """
    __tablename__ = 'favourites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False, index=True)
    recipe_title = db.Column(db.String(200), nullable=False)
    recipe_image = db.Column(db.String(200), nullable=False)

    recipe = db.relationship('Recipe', backref=db.backref('favourites', cascade="all, delete"))


class Recipe(db.Model):
    """ Table for Recipes """
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    serves = db.Column(db.String(50), nullable=True)
    prep_time = db.Column(db.String(50), nullable=True)
    cook_time = db.Column(db.String(50), nullable=True)
    age_group = db.Column(db.String(50), nullable=True, index=True)
    ingredients = db.Column(db.Text, nullable=True)
    method = db.Column(db.Text, nullable=True)
    recipe_url = db.Column(db.String(200), nullable=True)
    dietary_info = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    views = db.Column(db.Integer, default=0, nullable=True, index=True)
    last_viewed = db.Column(db.DateTime, nullable=True, index=True)

    def log_view(self) -> None:
        """Increment the view count and update the last viewed date."""
        from mod.datetime_utils import get_utc_now
        
        # Convert views to integer if it's a string
        if isinstance(self.views, str):
            self.views = int(self.views) if self.views.isdigit() else 0

        self.views = self.views + 1 if self.views is not None else 1
        self.last_viewed = get_utc_now()
        db.session.add(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Recipe instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'serves': self.serves,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'age_group': self.age_group,
            'ingredients': json.loads(self.ingredients) if self.ingredients else [],  # Convert JSON to list
            'method': json.loads(self.method) if self.method else [],  # Convert JSON to list
            'recipe_url': self.recipe_url,
            'dietary_info': self.dietary_info,
            'image_url': self.image_url,
            'views': self.views,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None
        }


# Association table for many-to-many relationship between meal plans and recipes
meal_plan_recipes = db.Table('meal_plan_recipes',
                             db.Column('meal_plan_id', db.Integer, db.ForeignKey('meal_plan.id'), primary_key=True),
                             db.Column('recipe_id', db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
                             )


class MealPlan(db.Model):
    __tablename__ = 'meal_plan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('Users', backref=db.backref('meal_plans', lazy=True))
    recipes = db.relationship('Recipe', secondary='meal_plan_recipes', backref='meal_plans')
    days = db.relationship('MealPlanDay', backref='meal_plan', lazy='joined', cascade='all, delete-orphan')


class MealPlanDay(db.Model):
    __tablename__ = 'meal_plan_day'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)  # e.g., 'Monday', 'Tuesday'
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plan.id'), nullable=False, index=True)

    breakfast_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True, index=True)
    lunch_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True, index=True)
    dinner_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True, index=True)

    breakfast = db.relationship('Recipe', foreign_keys=[breakfast_id])
    lunch = db.relationship('Recipe', foreign_keys=[lunch_id])
    dinner = db.relationship('Recipe', foreign_keys=[dinner_id])
