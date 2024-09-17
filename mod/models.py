from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from mod import db
from datetime import datetime

# Association table for the many-to-many relationship
user_favourites = db.Table('user_favourites',
                           db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                           db.Column('favourite_id', db.Integer, db.ForeignKey('favourites.id'), primary_key=True)
                           )


class Users(UserMixin, db.Model):
    """ Table for users """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_image = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # Relationship to Favourites
    favourites = db.relationship('Favourites', secondary=user_favourites, backref=db.backref('users', lazy='dynamic'))


class Favourites(db.Model):
    """ Table for Favourites """
    __tablename__ = 'favourites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    recipe_title = db.Column(db.String(200), nullable=False)
    recipe_image = db.Column(db.String(200), nullable=False)


class Recipe(db.Model):
    """ Table for Recipes """
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    serves = db.Column(db.String(50), nullable=True)
    prep_time = db.Column(db.String(50), nullable=True)
    cook_time = db.Column(db.String(50), nullable=True)
    age_group = db.Column(db.String(50), nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    method = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    views = db.Column(db.Integer, default=0)
    last_viewed = db.Column(db.DateTime, nullable=True)

    def log_view(self):
        """Increment the view count and update the last viewed date."""
        self.views = self.views + 1 if self.views is not None else 1
        self.last_viewed = datetime.utcnow()
        db.session.add(self)

    def to_dict(self):
        """Convert the Recipe instance to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'serves': self.serves,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'age_group': self.age_group,
            'ingredients': self.ingredients,
            'method': self.method,
            'url': self.url,
            'image_url': self.image_url,
            'views': self.views,
            'last_viewed': self.last_viewed.isoformat() if self.last_viewed else None
        }
