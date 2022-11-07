import os
import tempfile
from collections import Counter
from base64 import b64encode

import pytest

from app import create_app, db
from app.models import User, UserRoles


class TestConfig:
    ENV='test'
    DEBUG=True
    SQLALCHEMY_ECHO=True
    ADMIN_EMAIL = 'admin@email.email'
    USER_EMAIL = 'email@email.email'
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


def test_create_user(client):

    admin = User(email=TestConfig.ADMIN_EMAIL, role=UserRoles.admin, hub_id=1)
    admin.set_password(TestConfig.PASSWORD)
    db.session.add(admin)
    db.session.commit()

    rv = client.post(
        '/api/user',
        follow_redirects=True,
        json={
            'email': TestConfig.USER_EMAIL,
            'password': TestConfig.PASSWORD
        }
    )
    user = rv.json
    assert (
        user['email'] == TestConfig.USER_EMAIL
    )
    basic = b64encode(bytes(f"{TestConfig.ADMIN_EMAIL}:{TestConfig.PASSWORD}", encoding='utf-8')).decode('utf-8')
    rv = client.get(
        '/api/token',
        headers = {
            'Authorization': f"Basic {basic}"
        },
        follow_redirects=True
    )
    data = rv.json
    assert 'token' in data
    token = data['token']
    rv = client.put(
        f'/api/user/{user["id"]}',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        json={
            'role': 'validator',
            'categories': [1],
            'projects': [1],
            'position': 'validator'
        },
        follow_redirects=True
    )
    data = rv.json
    print(data)
    assert (
        data['id'] == user['id'] and
        data['role']['name'] == 'validator' and
        data['position'] == 'validator' and
        Counter(data['categories']) == Counter([1]) and
        Counter(data['projects']) == Counter([1])
    )
    rv = client.get(
        '/api/positions',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        follow_redirects=True
    )
    data = rv.json
    assert (
        len(data) == 1 and
        data[0]['name'] == 'validator'
    )
    rv = client.get(
        '/api/roles',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        follow_redirects=True
    )
    data = rv.json
    assert (
        len(data) == 7 and
        data[0]['name'] == 'default'
    )
    rv = client.get(
        '/api/responsibilities',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        query_string={
            'categories': [1],
            'project_id': 1
        },
        follow_redirects=True
    )
    data = rv.json
    print(data)
    assert (
        len(data) == 1 and
        data['1']['position'] == 'validator' and
        data['1']['users'][0]['email'] == TestConfig.USER_EMAIL
    )
    rv = client.put(
        f'/api/user/{user["id"]}',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        json={
            'role': 'validator',
            'categories': [2],
            'projects': [2],
            'position': 'validator'
        },
        follow_redirects=True
    )
    data = rv.json
    assert (
        (data['id'] == user['id']) and
        (data['role']['name'] == 'validator') and
        (data['position'] == 'validator') and
        Counter(data['categories']) == Counter([2]) and
        Counter(data['projects']) == Counter([2])
    )
    rv = client.get(
        '/api/responsibilities',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        query_string={
            'categories': [1],
            'project_id': 1
        },
        follow_redirects=True
    )
    data = rv.json
    assert (
        len(data) == 0
    )
