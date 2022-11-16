import jwt

from flask_httpauth import HTTPTokenAuth
from flask import current_app

from app.api.errors import error_response


token_auth = HTTPTokenAuth()


@token_auth.verify_token
def verify_token(token):
    try:
        user = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'],
            leeway=600
        )
    except:
        return None
    return user


@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)


@token_auth.get_user_roles
def get_user_roles(user):
    return user['role']['name']
