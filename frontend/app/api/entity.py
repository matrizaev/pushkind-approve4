from json.decoder import JSONDecodeError

from flask import abort, flash
from flask_login import current_user
import requests


class EntityApi():
    __entity_name__ = ''
    __entities_name__ = ''
    __service_host__ = ''

    @classmethod
    def get_entities(cls, **params) -> "list[dict]":
        headers = {
            'Authorization': f'Bearer {current_user.token}'
        }
        try:
            response = requests.get(f'http://{cls.__service_host__}/api/{cls.__entities_name__}', params=params, headers=headers)
        except requests.exceptions.ConnectionError:
            abort(503)
        try:
            json_response = response.json()
        except JSONDecodeError:
            abort(500)
        if response.status_code != 200:
            if 'message' in json_response:
                flash(json_response['message'])
        if 400 <= response.status_code <= 499:
            return None
        elif response.status_code != 200:
            abort(response.status_code)
        return json_response


    @classmethod
    def post_entity(cls, **params) -> dict:
        if hasattr(current_user, 'token'):
            headers = {
                'Authorization': f'Bearer {current_user.token}'
            }
        else:
            headers = None
        try:
            response = requests.post(f'http://{cls.__service_host__}/api/{cls.__entity_name__}', json=params, headers=headers)
        except requests.exceptions.ConnectionError:
            abort(503)
        try:
            json_response = response.json()
        except JSONDecodeError:
            abort(500)
        if response.status_code != 201:
            if 'message' in json_response:
                flash(json_response['message'])
        if 400 <= response.status_code <= 499:
            return None
        elif response.status_code != 201:
            abort(response.status_code)
        return json_response


    @classmethod
    def put_entity(cls, entity_id, **params) -> dict:
        headers = {
            'Authorization': f'Bearer {current_user.token}'
        }
        try:
            response = requests.put(f'http://{cls.__service_host__}/api/{cls.__entity_name__}/{entity_id}', json=params, headers=headers)
        except requests.exceptions.ConnectionError:
            abort(503)
        try:
            json_response = response.json()
        except JSONDecodeError:
            abort(500)
        if response.status_code != 200:
            if 'message' in json_response:
                flash(json_response['message'])
        if 400 <= response.status_code <= 499:
            return None
        elif response.status_code != 200:
            abort(response.status_code)
        return json_response


    @classmethod
    def delete_entity(cls, entity_id) -> dict:
        headers = {
            'Authorization': f'Bearer {current_user.token}'
        }
        try:
            response = requests.delete(f'http://{cls.__service_host__}/api/{cls.__entity_name__}/{entity_id}', headers=headers)
        except requests.exceptions.ConnectionError:
            abort(503)
        try:
            json_response = response.json()
        except JSONDecodeError:
            abort(500)
        if response.status_code != 200:
            if 'message' in json_response:
                flash(json_response['message'])
        if 400 <= response.status_code <= 499:
            return None
        elif response.status_code != 200:
            abort(response.status_code)
        return json_response
