from flask import Blueprint, flash, redirect, url_for, render_template, session
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from db.database import session_scope
from db.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import json

main_blueprint = Blueprint("main", __name__)

# Формы регистрации и авторизации
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=36)])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(max=100, min=4)])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=36)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])


# Маршруты
@main_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
        if user:
            flash('Пользователь с этой почтой уже зарегистрирован', category='danger')
            return redirect(url_for('main.register', form=form, genres=get_genres()))
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        with session_scope() as session:
            session.add(user)
        flash('Вы успешно зарегистрировались!', category='success')
    elif form.errors:
        flash(form.errors, category='danger')
    return render_template('register.html', form=form, genres=get_genres())

@main_blueprint.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                return redirect(url_for('main.main_route'))
        flash('Не удалось войти в аккаунт', category='danger')
    return render_template('login.html', form=form, genres=get_genres())

@main_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main_blueprint.route('/main')
@main_blueprint.route('/')
@login_required
def main_route():
    print(current_user.username)
    return render_template('home.html', username=current_user.username, genres=get_genres())



# Дополнительные функции
def get_genres():
    with open ('static/json/books_catalog.json', encoding='utf-8') as file:
        books = json.load(file)
    genres = []
    for book in books:
        genres.append(book['genre'])
    return sorted(list(set(genres)))