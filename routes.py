from functools import wraps
from flask import Blueprint, flash, redirect, url_for, render_template, session, request
from flask_login import login_user, login_required, logout_user, current_user
from db.database import session_scope
from db.models import User, Book
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm


main_blueprint = Blueprint("main", __name__)

def anonymous_required(f):
    """
    Декоратор для доступа только неавторизованным пользователям
    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('main.main_route'))  # Перенаправление на главную страницу
        return f(*args, **kwargs)
    return decorated_function

@main_blueprint.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
        if user:
            flash('Пользователь с такой почтой уже зарегистрирован', category='danger')
            return redirect(url_for('main.register', form=form, genres=get_genres()))
        with session_scope() as session:
            user = session.query(User).filter_by(phone=form.phone.data).first()
        if user:
            flash('Пользователь с таким номером телефона уже зарегистрирован', category='danger')
            return redirect(url_for('main.register', form=form, genres=get_genres()))
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            password_hash=generate_password_hash(form.password.data)
        )
        with session_scope() as session:
            session.add(user)
        flash('Вы успешно зарегистрировались!', category='success')
    elif form.errors:
        flash(form.errors, category='danger')
    return render_template('register.html', form=form, genres=get_genres())

@main_blueprint.route('/login', methods=["GET", "POST"])
@anonymous_required
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

@main_blueprint.route('/', methods=['GET', 'POST'])
def main_route():
    if request.method == 'GET':
        return search_by_title('search')
    username = get_username()
    return render_template('home.html',
                           username=username, genres=get_genres(), top_books=get_top_books())

@main_blueprint.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    return render_template('cart.html')

@main_blueprint.route('/genre/<int:num>', methods=['GET', 'POST'])
def genre_books(num):
    genre = get_genres()[num-1]
    books = get_by_genre(genre)
    username = get_username()
    return render_template('genre.html', books=books, genre=genre,
                           username=username, genres=get_genres())

@main_blueprint.route('/book/<int:id>', methods=['GET', 'POST'])
def book(id):
    username = get_username()
    books = get_books()
    book = next((book for book in books if book.get('id') == id), None)
    return render_template('book.html', book=book,
                           username=username, genres=get_genres())


# Дополнительные функции
def get_username():
    if current_user.is_authenticated:
        return current_user.username
    else:
        return False

def get_genres():
    books = get_books()
    genres = []
    for book in books:
        genres.append(book['genre'])
    return sorted(list(set(genres)))

def obj_to_dict(books):
    return [{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "price": book.price,
        "genre": book.genre,
        "cover": book.cover,
        "description": book.description,
        "rating": book.rating,
        "year": book.year
    } for book in books]

def get_books() -> list[dict]:
    with session_scope() as session:
        books = session.query(Book).all()
        return obj_to_dict(books)

def get_top_books():
    books = get_books()
    return sorted(books, key=lambda x: x['rating'], reverse=True)[:3]

def get_by_genre(genre):
    books = get_books()
    genre_books = []
    for book in books:
        if book['genre'] == genre:
            genre_books.append(book)
    return genre_books

def search_by_title(search):
    search_query = request.args.get(search, '').strip()
    username = get_username()
    if search_query:
        with session_scope() as session:
            books = session.query(Book).filter(Book.title.ilike(f'%{search_query}%')).all()
            books = obj_to_dict(books)
            if books:
                if len(books) == 1:
                    return redirect(url_for("main.book", id=books[0]['id']))
                return render_template('home.html',
                                       username=username, genres=get_genres(), top_books=get_top_books(), search_results=books)
            flash('По Вашему запросу ничего не найдено.', category='info')
    return render_template('home.html',
                           username=username,
                           genres=get_genres(),
                           top_books=get_top_books())

