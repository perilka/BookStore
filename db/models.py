from flask_login import UserMixin

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    email = Column(String(120), unique=True)
    phone = Column(String(12), unique=True)
    password_hash = Column(String(256))

class Book(Base, UserMixin):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(80))
    author = Column(String(80))
    price = Column(Float)
    genre = Column(String(80))
    cover = Column(String)
    description = Column(String)
    rating = Column(Float)
    year = Column(Integer)