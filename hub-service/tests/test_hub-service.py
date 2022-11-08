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
    hub = post_entity(client, token, 'hub', {'name': 'name', 'email': 'email1'})
    assert 'id' in hub
    assert hub['name'] == 'name'

    vendor = post_entity(client, token, 'vendor', {'name': 'name', 'email': 'email2'})
    assert vendor['name'] == 'name'

    category = post_entity(client, token, 'category', {'name': 'name'})
    assert category['name'] == 'name'

    product = post_entity(
        client,
        token,
        'product',
        {
            'name': 'name',
            'sku': 'sku',
            'vendor_id': vendor['id'],
            'category': category['name'],
            'measurement': 'measurement',
            'description': 'description',
            'price': 0.0
        }
    )
    assert product['name'] == 'name'

    put_entities(client, token, 'hub', hub['id'], {'name': 'new_name'})
    put_entities(client, token, 'vendor', vendor['id'], {'name': 'new_name'})
    put_entities(client, token, 'category', category['id'], {'name': 'new_name'})
    put_entities(client, token, 'product', product['id'], {'name': 'new_name'})

    delete_entity(client, token, 'product', product['id'])
    delete_entity(client, token, 'category', category['id'])
    delete_entity(client, token, 'vendor', vendor['id'])

    vendors = get_entities(client, token, 'vendors')
    assert len(vendors) == 0
    categories = get_entities(client, token, 'categories')
    assert len(categories) == 0
    products = get_entities(client, token, 'products')
    assert len(products) == 0

    delete_entity(client, token, 'hub', hub['id'])
    hubs = get_entities(client, token, 'hubs')
    assert len(hubs) == 0
