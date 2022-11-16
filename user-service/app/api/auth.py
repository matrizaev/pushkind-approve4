from datetime import datetime, timezone

from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth

from app.models import User
from app import db
from app.api.errors import error_response



basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()
token_auth_renew = HTTPTokenAuth()
multi_auth = MultiAuth(basic_auth, token_auth_renew)


@basic_auth.verify_password
def verify_password(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        user.last_seen = datetime.now(tz=timezone.utc)
        db.session.commit()
        return user


@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)


@token_auth.verify_token
def verify_token(token):
    return User.verify_token(token, leeway=600)


@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)


@token_auth_renew.verify_token
def verify_token_renew(token):
    return User.verify_token(token, verify_exp=False)


@token_auth_renew.error_handler
def token_auth_error_renew(status):
    return error_response(status)


@token_auth.get_user_roles
def get_user_roles(user):
    return user.role
