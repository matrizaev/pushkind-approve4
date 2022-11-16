import socket
import logging
from time import sleep

import pika


logging.basicConfig(level=logging.INFO)


def wait_for_port_open(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    while not connected:
        try:
            s.connect((host,port))
            connected = True
        except Exception as e:
            logging.info('The RabbitMQ is not available. Waiting.')
            sleep(10)
            continue
    s.close()


def callback_hub_changed(ch, method, properties, body):
    import json
    from app import db
    from app.models import Order
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        if removed:
            Order.query.filter_by(hub_id=hub_id).delete()
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    wait_for_port_open('mq-service', 5672)
    logging.info('The RabbitMQ is available. Proceeding.')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()

    channel.exchange_declare(exchange='hub_changed', exchange_type='fanout')
    channel.queue_declare(queue='hub_changed_order')
    channel.queue_bind(exchange='hub_changed', queue='hub_changed_order')

    channel.basic_consume(queue='hub_changed_order', on_message_callback=callback_hub_changed)

    channel.start_consuming()

if __name__ == '__main__':
    main()
