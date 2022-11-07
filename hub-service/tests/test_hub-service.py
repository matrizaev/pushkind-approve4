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


def test_create_hub(client):

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
    rv = client.post(
        '/api/hub',
        follow_redirects=True,
        json={
            'email': TestConfig.ADMIN_EMAIL,
            'name': 'hub'
        },
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    hub = rv.json
    assert (
        hub['id'] == 1 and
        hub['email'] == TestConfig.ADMIN_EMAIL
    )

    rv = client.post(
        '/api/vendor',
        follow_redirects=True,
        json={
            'email': TestConfig.USER_EMAIL,
            'name': 'vendor'
        },
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    vendor = rv.json
    assert (
        vendor['id'] == 2 and
        vendor['email'] == TestConfig.USER_EMAIL
    )

    rv = client.post(
        '/api/vendor',
        follow_redirects=True,
        json={
            'email': TestConfig.USER_EMAIL2,
            'name': 'vendor2'
        },
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    vendor = rv.json
    assert (
        vendor['id'] == 3 and
        vendor['email'] == TestConfig.USER_EMAIL2 and
        vendor['name'] == 'vendor2'
    )

    rv = client.delete(
        '/api/vendor/3',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    status = rv.json
    assert status['status'] == 'success'

    rv = client.get(
        '/api/hubs',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    hubs = rv.json
    assert (
        len(hubs) == 1
    )

    rv = client.delete(
        '/api/hub/1',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    status = rv.json
    assert status['status'] == 'success'

    rv = client.get(
        '/api/hubs',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    hubs = rv.json
    assert (
        len(hubs) == 0
    )
