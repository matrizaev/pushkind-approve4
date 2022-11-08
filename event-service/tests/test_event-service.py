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


def test_manage_entities(client, token):
    event = post_entity(client, token, 'event', {'data': 'data', 'event_type': 'commented'})
    assert event['data'] == 'data' and event['event_type']['name'] == 'commented'

    events = get_entities(client, token, 'events')
    assert len(events) == 1
    assert events[0]['data'] == 'data' and events[0]['event_type']['name'] == 'commented'
