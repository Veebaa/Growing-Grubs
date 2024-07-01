from sqlalchemy import Integer, String, create_engine, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///growinggrubs.db', echo=True)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)


class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    ingredients = Column(String(255), nullable=False)
    instructions = Column(String(255), nullable=False)


Base.metadata.create_all(engine)

print("Database initialized successfully")

users = session.query(Users).all()
for user in users:
    print(f"ID: {user.id}, Name: {user.first_name} {user.last_name}, Email: {user.email}")
