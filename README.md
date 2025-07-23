# Bookstore Web App

Веб-приложение интернет-магазина книг на Flask с поддержкой регистрации, корзины, оформления заказов и отзывов.

## Возможности

- Регистрация и авторизация пользователей  
- Просмотр каталога книг с обложками, рейтингом и описанием  
- Добавление книг в корзину  
- Оформление заказов с выбором адреса доставки  
- Оставление отзывов и оценок к книгам  
- Панель управления заказами (по статусам)  

## Технологии

- **Backend**: Flask, SQLAlchemy  
- **Аутентификация**: Flask-Login  
- **Формы и валидация**: Flask-WTF  
- **База данных**: PostgreSQL  
- **Конфигурация**: Pydantic + `.env`  
- **Прочее**: HTML-шаблоны Jinja2, Bootstrap, логирование  


## Установка и запуск

1. **Клонируйте этот репозиторий**

2. **Создайте и активируйте виртуальное окружение**

```bash
python -m venv venv
source venv/bin/activate
venv\Scripts\activate.bat
```

3. **Установите зависимости**

```bash
pip install -r requirements.txt
```

4. **Создайте файл .env (пример):**

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/your_database
SECRET_KEY=your_secret_key
APP_PORT=5000
DEBUG=True
```

5. **Заполните таблицу книг**

Запустите скрипт для загрузки данных из static/json/books_catalog.json:
```bash
python migrate_books.py
```

6. **Запустите приожение**

```bash
python app.py
```

