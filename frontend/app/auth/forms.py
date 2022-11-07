from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.validators import Length
from wtforms.fields import EmailField



class LoginForm(FlaskForm):
    email = EmailField(
        'Электронная почта',
        validators=[
            DataRequired(message='Электронная почта - обязательное поле.'),
            Email(message='Некорректный адрес электронной почты.')
        ]
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired(message='Пароль - обязательное поле.')]
    )
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Авторизация')


class RegistrationForm(FlaskForm):
    email = EmailField(
        'Электронная почта',
        validators=[
            DataRequired(message='Электронная почта - обязательное поле.'),
            Email(message='Некорректный адрес электронной почты.'),
            Length(max=128, message='Слишком длинный электронный адрес.')
        ]
    )
    password = PasswordField(
        'Пароль',
        validators=[DataRequired(message='Пароль - обязательное поле.')]
    )
    password2 = PasswordField(
        'Повторите пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message='Пароли не совпадают.')
        ]
    )
    submit = SubmitField('Регистрация')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(
        'Электронная почта',
        validators=[
            DataRequired(message='Электронная почта - обязательное поле.'),
            Email(message='Некорректный адрес электронной почты.')
        ]
    )
    submit = SubmitField('Сбросить')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'Пароль',
        validators=[DataRequired(message='Пароль - обязательное поле.')]
    )
    password2 = PasswordField(
        'Повторите пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message='Пароли не совпадают.')
        ]
    )
    submit = SubmitField('Сменить')
