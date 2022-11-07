#from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, current_app
from flask import request, session
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse

from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_password_reset_email, send_user_registered_email
from app.auth import bp
from app.api.user import UserApi, User


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.show_index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        token = UserApi.get_token(email, password)
        if token is None:
            flash('Некорректный логин или пароль.')
            return redirect(url_for('auth.login'))
        user = UserApi.decode_user(token)
        login_user(User(user), remember=form.remember_me.data)
        current_app.logger.info('%s logged', email)
        return redirect(url_for('main.show_index'))
    for error in form.email.errors + form.password.errors + form.remember_me.errors:
        flash(error)
    return render_template('auth/login.html', form=form)


@bp.route('/login/<token>/', methods=['GET'])
def login_token(token):
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('main.show_index')

    if not current_user.is_authenticated:
        user = UserApi.decode_user(token)
        login_user(User(user), remember=False)
        current_app.logger.info('%s logged', user.email)

    return redirect(next_page)


@bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated and current_user.role.name != 'admin':
        return redirect(url_for('main.show_index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        user = UserApi.post_entity(email=email, password=password)
        if user is None:
            return redirect(url_for('auth.signup'))
        flash('Теперь пользователь может войти.')
        current_app.logger.info('%s registered', email)
        if current_user.is_authenticated and current_user.role.name == 'admin':
            return redirect(url_for('main.show_users'))
        return redirect(url_for('auth.login'))
    for error in form.email.errors + form.password.errors + form.password2.errors:
        flash(error)
    return render_template('auth/register.html', form=form)


@bp.route('/logout/')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/request/', methods=['GET', 'POST'])
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('main.show_index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
            flash('На вашу электронную почту отправлен запрос на сброс пароля.')
            return redirect(url_for('auth.login'))
        flash('Такой пользователь не обнаружен.')
    else:
        for error in form.email.errors:
            flash(error)
    return render_template('auth/request.html', form=form)


@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.show_index'))
    user = User.verify_jwt_token(token)
    if not user:
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_passwors(form.password.data)
        db.session.commit()
        flash('Ваш пароль был изменён.')
        return redirect(url_for('auth.login'))
    for error in form.password.errors + form.password2.errors:
        flash(error)
    return render_template('auth/reset.html', form=form)
