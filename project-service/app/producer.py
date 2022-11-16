import json

import pika


def post_entity_changed(hub_id, entity_name, data, operation):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    channel.exchange_declare(exchange=f'{entity_name}_changed', exchange_type='fanout')
    body = {
        'hub_id': hub_id,
        operation: data
    }
    channel.basic_publish(exchange=f'{entity_name}_changed', routing_key='', body=json.dumps(body))
    connection.close()
