import os
import tempfile

import pytest
import jwt

from app import create_app, db


class TestConfig:
    ENV='test'
    DEBUG=True
    SQLALCHEMY_ECHO=True
    ADMIN = {
        'id': 1,
        'email': 'admin@email.email',
        'name': None,
        'location': None,
        'phone': None,
        'position': None,
        'role': {
            'name': 'admin'
        },
        'hub_id': 1
    }
    SECRET_KEY = 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = ''
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MOMENT_DEFAULT_FORMAT = 'DD.MM.YYYY HH:mm'
    PASSWORD = 'password'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    TestConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def token():
    return jwt.encode(
        TestConfig.ADMIN,
        TestConfig.SECRET_KEY,
        algorithm='HS256'
    )
