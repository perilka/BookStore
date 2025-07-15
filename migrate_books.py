import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Book
from config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    if session.query(Book).first() is None:
        logger.info("Таблица books пуста. Начинается перенос данных из JSON")
        with open('static/json/books_catalog.json', 'r', encoding='utf-8') as file:
            books = json.load(file)
        for book_dict in books:
            book = Book(
                title=book_dict['title'],
                author=book_dict['author'],
                price=book_dict['price'],
                genre=book_dict['genre'],
                cover=book_dict['cover'],
                description=book_dict['description'],
                rating=book_dict['rating'],
                year=book_dict['year']
            )
            session.merge(book)
        session.commit()
        logger.info("Данные успешно перенесены в таблицу books.")
    else:
        logger.info("Таблица books уже содержит данные. Перенос пропущен.")
except Exception as e:
    logger.error(f"Ошибка при переносе данных: {e}")
    session.rollback()
finally:
    session.close()
    logger.info("Сессия закрыта.")