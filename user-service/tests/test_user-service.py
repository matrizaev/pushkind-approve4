from collections import Counter
from base64 import b64encode


def post_entity(client, token: "str", name: "str", data: "dict") -> "dict":
    rv = client.post(
        f'/api/{name}',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        },
        json=data
    )
    data = rv.json
    assert rv.status_code == 201
    assert isinstance(data, dict)
    return data


def delete_entity(client, token: "str", name: "str", entity_id: "int") -> None:
    rv = client.delete(
        f'/api/{name}/{entity_id}',
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert rv.status_code == 200
    assert isinstance(data, dict)
    assert data['status'] == 'success'


def put_entities(client, token: "str", name: "str", entity_id: "int", data: "dict") -> None:
    rv = client.put(
        f'/api/{name}/{entity_id}',
        headers = {
            'Authorization': f'Bearer {token}'
        },
        json=data
    )
    new_data = rv.json
    assert rv.status_code == 200
    assert isinstance(new_data, dict)
    for k, v in data.items():
        if isinstance(new_data[k], dict):
            assert new_data[k]['name'] == v
        else:
            assert new_data[k] == v


def get_entities(client, token: "str", name: "str") -> "dict":
    rv = client.get(
        f'/api/{name}',
        follow_redirects=True,
        headers = {
            'Authorization': f'Bearer {token}'
        }
    )
    data = rv.json
    assert rv.status_code == 200
    assert isinstance(data, list)
    return data

def get_token(client):
    basic = b64encode(bytes("admin@email.email:123456", encoding='utf-8')).decode('utf-8')
    rv = client.get(
        '/api/token',
        headers = {
            'Authorization': f"Basic {basic}"
        },
        follow_redirects=True
    )
    data = rv.json
    assert 'token' in data
    return data['token']


def test_manage_entities(client):

    token = get_token(client)

    user = post_entity(client, token, 'user', {'email': 'email', 'password': '123456'})
    assert 'id' in user
    assert user['email'] == 'email'

    put_entities(
        client,
        token,
        'user',
        user['id'],
        {
            'name': 'new_name',
            'role': 'validator',
            'position': 'validator',
            'projects': ['project'],
            'categories': ['category']
        }
    )

    positions = get_entities(client, token, 'positions')
    assert (
        len(positions) == 1 and
        positions[0]['name'] == 'validator'
    )

    delete_entity(client, token, 'user', user['id'])
    users = get_entities(client, token, 'users')
    assert len(users) == 1
