from types import SimpleNamespace

import jwt
from flask import current_app, flash
from flask_login import UserMixin
import requests
from requests.auth import HTTPBasicAuth

from app.api.entity import EntityApi


USER_SERVICE_HOST = 'user-service:5000'

class User(UserMixin):
    __slots__ = (
        'id',
        'email',
        'name',
        'phone',
        'location',
        'position',
        'role',
        'hub_id',
        'token'
    )
    def __init__(self, json_data):
        self.token = json_data['token']
        self.id = json_data['id']
        self.email = json_data['email']
        self.name = json_data['name']
        self.phone = json_data['phone']
        self.location = json_data['location']
        self.position = json_data['position']
        self.role = SimpleNamespace(**json_data['role'])
        self.hub_id = json_data['hub_id']

    def get_id(self):
        return self.token

    def __str__(self) -> str:
        data = {
            'id': self.id,
            'token': self.token,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'hub_id': self.hub_id
        }
        return str(data)


class UserApi(EntityApi):
    __entity_name__ = 'user'
    __entities_name__ = 'users'
    __service_host__ = USER_SERVICE_HOST


    @classmethod
    def get_token(cls, email, password, token=None):
        if token is not None:
            headers = {
                'Authorization': f'Bearer {token}'
            }
            auth = None
        else:
            headers = None
            auth = HTTPBasicAuth(email, password)
        try:
            response = requests.get(f'http://{cls.__service_host__}/api/token', auth=auth, headers=headers)
        except requests.exceptions.ConnectionError:
            return None
        json_response = response.json()
        if response.status_code != 200:
            if 'message' in json_response:
                flash(json_response['message'])
            return None
        return json_response.get('token')


    @classmethod
    def decode_user(cls, token):
        try:
            user = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
        except:
            return None
        user['token'] = token
        return user


class RoleApi(EntityApi):
    __entity_name__ = 'role'
    __entities_name__ = 'roles'
    __service_host__ = USER_SERVICE_HOST


class PositionApi(EntityApi):
    __entity_name__ = 'position'
    __entities_name__ = 'positions'
    __service_host__ = USER_SERVICE_HOST


class ResponsibilityApi(EntityApi):
    __entity_name__ = 'responsibility'
    __entities_name__ = 'responsibilities'
    __service_host__ = USER_SERVICE_HOST
