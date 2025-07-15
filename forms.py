from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[InputRequired(), Email()])
    password = PasswordField('Пароль', validators=[InputRequired(), Length(min=8, max=36)])


class RegistrationForm(FlaskForm):
    username = StringField('Имя', validators=[InputRequired(), Length(max=100, min=4)])
    email = StringField('Почта', validators=[InputRequired(), Email()])
    phone = StringField('Номер телефона', validators=[InputRequired(), Length(min=12, max=12)])
    password = PasswordField('Пароль', validators=[InputRequired(), Length(min=8, max=36)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[InputRequired(), EqualTo('password')])

    def validate_phone(self, phone):
        phone_value = phone.data
        if not phone_value.startswith('+7') or not phone_value[2:].isdigit() or len(phone_value[2:]) != 10:
            raise ValidationError('Номер телефона должен быть в формате +7XXXXXXXXXX (11 цифр, начиная с +7).')