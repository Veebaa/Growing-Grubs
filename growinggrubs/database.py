from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

engine = create_engine('sqlite:///growinggrubs.db', echo=True)

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(String(100), nullable=False)
    last_name = db.Column(String(100), nullable=False)
    email = db.Column(String(100), nullable=False)
    password = db.Column(String(100), nullable=False)

class Recipe(Base):
     __tablename__ = 'recipes'

     id = db.Column(Integer, primary_key=True, autoincrement=True)
     name = db.Column(String(100), nullable=False)
     ingredients = db.Column(String(255), nullable=False)
     instructions = db.Column(String(255), nullable=False)

Base.metadata.create_all(engine)

print("Database initialized successfully")

users = session.query(User).all()
for user in users:
    print(f"ID: {user.id}, Name: {user.first_name} {user.last_name}, Email: {user.email}")
