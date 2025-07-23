from functools import wraps
from flask import Blueprint, flash, redirect, url_for, render_template, session, request
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.orm import subqueryload

from db.database import session_scope
from db.models import User, Book, CartItem, Review, Order, OrderStatus, OrderItem
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm
import random
from datetime import datetime


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

@main_blueprint.route('/genre/<int:num>')
def genre_books(num):
    genre = get_genres()[num-1]
    books = get_by_genre(genre)
    username = get_username()
    return render_template('genre.html', books=books, genre=genre,
                           username=username, genres=get_genres())


@main_blueprint.route('/book/<int:id>')
def book(id):
    username = get_username()
    books = get_books()
    reviews = get_reviews(id)
    book = next((book for book in books if book.get('id') == id), None)
    return render_template('book.html', book=book,
                           username=username, genres=get_genres(), reviews=reviews)


@main_blueprint.route('/cart')
@login_required
def cart():
    username = get_username()
    user_id = current_user.id
    cart_items = get_cart_items(user_id)
    if cart_items:
        return render_template('cart.html',
                           username=username, genres=get_genres(), cart_items=cart_items)
    flash('В Вашей корзине пока ничего нет :(')
    return render_template('cart.html',
                           username=username, genres=get_genres())


@main_blueprint.route('/cart/add/<int:book_id>', methods=['POST', 'GET'])
@login_required
def add_to_cart(book_id):
    amount = int(request.form.get('amount', 1)) if request.method == 'POST' else 1
    if amount <= 0:
        flash('Количество должно быть больше 0.', category='error')
        return redirect(url_for('main.book', id=book_id))
    with session_scope() as session:
        book = session.query(Book).get(book_id)
        if not book:
            flash('Книга не найдена.', category='error')
            return redirect(url_for('main.main_route'))
        cart_item = session.query(CartItem).filter_by(
            user_id=current_user.id, book_id=book_id
        ).first()
        if cart_item:
            cart_item.amount += amount
            flash(f'Добавлено еще {amount} шт. "{book.title}" в корзину.', category='success')
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                book_id=book_id,
                amount=amount
            )
            session.add(cart_item)
            flash(f'Книга "{book.title}" добавлена в корзину.', category='success')
        session.commit()
        return redirect(url_for('main.book', id=book_id))


@main_blueprint.route('/cart/delete/<int:id>')
@login_required
def delete_from_cart(id):
    with session_scope() as session:
        item = session.query(CartItem).get(id)
        if not item or item.user_id != current_user.id:
            flash('Элемент корзины не найден или у Вас нет прав!!!!!!!!', category='error')
            return redirect(url_for('main.cart'))
        if item.amount == 1:
            session.delete(item)
        else:
            item.amount -= 1
        session.commit()
        return redirect(url_for('main.cart'))


@main_blueprint.route('/review/add/<int:book_id>', methods=["POST", "GET"])
@login_required
def add_review(book_id):
    review_text = request.form.get('review_text')
    grade = int(request.form.get('grade'))
    with session_scope() as session:
        book = session.query(Book).get(book_id)
        if not book:
            flash('Книга не найдена.', category='error')
            return redirect(url_for('main.main_route'))
        is_review = session.query(Review).filter_by(user_id=current_user.id, book_id=book_id).first()
        if is_review:
            flash(f'Вы уже оставляли отзыв для {book.title}', category='info')
            return redirect(url_for('main.book', id=book.id))
        else:
            review = Review(
                user_id=current_user.id,
                book_id=book_id,
                grade=grade,
                review_text=review_text
            )
            session.add(review)
            flash(f'Ваш отзыв для "{book.title}" отправлен.', category='success')
        session.commit()
        update_rating(review.id)
        return redirect(url_for('main.book', id=book_id))


@main_blueprint.route('/add_order', methods=["POST", "GET"])
@login_required
def add_order():
    if request.method == "POST":
        delivery_method = request.form.get('delivery_method')
        if delivery_method not in ('pickup', 'door'):
            flash('Неверный способ доставки.', 'error')
            return render_template('order.html')
        if delivery_method == 'door':
            address = request.form.get('address', '').strip()
            if not address:
                flash('Пожалуйста, введите адрес доставки.', 'error')
                return render_template('order.html')
        else:
            address = 'Самовывоз'
        with session_scope() as session:
            order = Order(
                user_id=current_user.id,
                created_at=datetime.utcnow(),
                status=OrderStatus.pending,
                address=address
            )
            session.add(order)
            session.flush()
            cart_items = session.query(CartItem).filter_by(user_id=current_user.id).all()
            if not cart_items:
                flash('Ваша корзина пуста.', 'error')
                return redirect(url_for('main.cart'))
            for ci in cart_items:
                oi = OrderItem(
                    order_id=order.id,
                    book_id=ci.book_id,
                    quantity=ci.amount,
                    price=ci.book.price
                )
                session.add(oi)
            for ci in cart_items:
                session.delete(ci)
            session.commit()
            flash('Ваш заказ успешно оформлен!', 'success')
            return redirect(url_for('main.cart'))
    return render_template('order.html')


@main_blueprint.route("/my_orders")
@login_required
def show_orders():
    username = get_username()
    with session_scope() as session:
        orders = session.query(Order).options(subqueryload(Order.order_items).subqueryload(OrderItem.book)).filter_by(user_id=current_user.id).all()
        orders_data = get_orders(orders)
    return render_template('my_orders.html',
                           username=username,
                           genres=get_genres(),
                           orders=orders_data)



def generate_confirmation_code(length=4):
    return ''.join(random.choices('0123456789', k=length))

def get_orders(orders):
    result = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "created_at": order.created_at.strftime('%Y-%m-%d %H:%M'),
            "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
            "address": order.address,
            "items": []
        }
        for item in order.order_items:
            item_dict = {
                "book_id": item.book_id,
                "title": item.book.title if item.book else "—",
                "quantity": item.quantity,
                "price": item.price
            }
            order_dict["items"].append(item_dict)
        result.append(order_dict)
    return result

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

def get_cart_items(user_id):
    with session_scope() as session:
        cart_items = session.query(CartItem).filter_by(user_id=user_id).all()
        return [
            {'id': item.id,
             'book_id': item.book.id,
             'book_title': item.book.title,
             'book_author': item.book.author,
             'amount': item.amount,
             'total_price': item.book.price * item.amount
             } for item in cart_items
        ]

def get_reviews(book_id):
    with session_scope() as session:
        reviews = session.query(Review).filter_by(book_id=book_id).all()
        return [
            {'id': review.id,
             'book_id': review.book.id,
             'username': review.user.username,
             'grade': review.grade,
             'review_text': review.review_text,
             } for review in reviews
        ]

def update_rating(rev_id):
    with session_scope() as session:
        review = session.query(Review).filter_by(id=rev_id).first()
        grade = review.grade
        old_rating = review.book.rating
        new_rating = round((grade + old_rating)/2, 1)
        review.book.rating = new_rating