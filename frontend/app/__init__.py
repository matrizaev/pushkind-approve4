import json

from flask import Flask, session
from flask_mail import Mail
from flask_login import LoginManager

from config import Config
from app.api.user import User, UserApi


login = LoginManager()
mail = Mail()


def to_json(value):
    return json.dumps(value)

@login.user_loader
def load_user(token):
    user = UserApi.decode_user(token)
    if user is None:
        token = UserApi.get_token(None, None, token)
        user = UserApi.decode_user(token)
        session["_user_id"] = token
    return User(user) if user else None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    login.init_app(app)
    mail.init_app(app)

    login.login_view = 'auth.login'
    login.login_message = 'Пожалуйста, авторизуйтесь, чтобы увидеть эту страницу.'

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    app.jinja_env.filters['to_json'] = to_json

    return app
