import os
import tempfile

import pytest
import jwt

from app import create_app, db


def get_token(user, secret_key):
    token = {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'role': user['role'],
        'hub_id': user['hub_id']
    }
    return jwt.encode(
        token,
        secret_key,
        algorithm='HS256'
    )


class TestConfig:
    ENV='test'
    DEBUG=True
    SQLALCHEMY_ECHO=True
    ADMIN_EMAIL = 'admin@email.email'
    USER_EMAIL = 'email@email.email'
    USER_EMAIL2 = 'email2@email2.email2'
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


def test_empty_db(client):
    """Start with a blank database."""
    rv = client.get('/')
    data = rv.json
    assert data['error'] == 'Not Found'


def test_get_entities(client):

    token = get_token(
        {
            'id': 1,
            'email': TestConfig.ADMIN_EMAIL,
            'name': 'admin',
            'role': {
                'name': 'admin'
            },
            'hub_id': 1
        },
        TestConfig.SECRET_KEY
    )

    rv = client.get(
        '/api/projects',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 0

    rv = client.get(
        '/api/sites',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 0

    rv = client.get(
        '/api/incomes',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 0

    rv = client.get(
        '/api/cashflows',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 0

    rv = client.get(
        '/api/order_limits',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 0

    rv = client.get(
        '/api/order_limit_intervals',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert len(data) == 6
