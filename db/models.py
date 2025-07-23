from flask_login import UserMixin

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from datetime import datetime
from sqlalchemy import DateTime, Enum

import enum


Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(12), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    cart_items = relationship("CartItem", back_populates="user")
    reviews = relationship("Review", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    author = Column(String(80), nullable=False)
    price = Column(Float, nullable=False)
    genre = Column(String(80), nullable=False)
    cover = Column(String, nullable=False)
    description = Column(String(500), nullable=False)
    rating = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)

    cart_items = relationship("CartItem", back_populates="book")
    reviews = relationship("Review", back_populates="book")

    __table_args__ = (
        CheckConstraint('rating > 0 AND rating <= 5', name='check_rating_range'),
        CheckConstraint('year > 0', name='check_year_positive'),
    )

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title})>"


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    amount = Column(Integer, nullable=False)

    user = relationship("User", back_populates="cart_items")
    book = relationship("Book", back_populates="cart_items")

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book'),
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, amount={self.amount})>"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    grade = Column(Integer, nullable=False)
    review_text = Column(String(500), nullable=False)

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book'),
        CheckConstraint('grade > 0 AND grade <= 5', name='check_grade_range'),
    )

    def __repr__(self):
        return f"<Review(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, grade={self.grade})>"


class OrderStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    canceled = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    address = Column(String(255), nullable=False)

    user = relationship("User", backref="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status}, created_at={self.created_at})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Цена на момент заказа

    order = relationship("Order", back_populates="order_items")
    book = relationship("Book")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('price >= 0', name='check_price_non_negative'),
    )

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, book_id={self.book_id}, quantity={self.quantity}, price={self.price})>"
