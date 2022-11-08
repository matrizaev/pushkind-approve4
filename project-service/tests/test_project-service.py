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
    project = post_entity(client, token, 'project', {'name': 'name'})
    assert 'id' in project
    assert project['name'] == 'name'

    site = post_entity(client, token, 'site', {'name': 'name', 'project_id': project['id']})
    assert 'id' in site
    assert site['name'] == 'name'

    income = post_entity(client, token, 'income', {'name': 'name'})
    assert 'id' in income
    assert income['name'] == 'name'

    cashflow = post_entity(client, token, 'cashflow', {'name': 'name'})
    assert 'id' in cashflow
    assert cashflow['name'] == 'name'

    put_entities(client, token, 'project', project['id'], {'name': 'new_name'})
    put_entities(client, token, 'site', site['id'], {'name': 'new_name'})
    put_entities(client, token, 'income', income['id'], {'name': 'new_name'})
    put_entities(client, token, 'cashflow', cashflow['id'], {'name': 'new_name'})

    delete_entity(client, token, 'project', project['id'])
    delete_entity(client, token, 'income', income['id'])
    delete_entity(client, token, 'cashflow', cashflow['id'])

    projects = get_entities(client, token, 'projects')
    assert len(projects) == 0
    sites = get_entities(client, token, 'sites')
    assert len(sites) == 0
    incomes = get_entities(client, token, 'incomes')
    assert len(incomes) == 0
    cashflows = get_entities(client, token, 'cashflows')
    assert len(cashflows) == 0
