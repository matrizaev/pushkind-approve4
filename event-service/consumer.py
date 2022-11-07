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


def main():
    wait_for_port_open('mq-service', 5672)
    logging.info('The RabbitMQ is available. Proceeding.')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()

    channel.exchange_declare(exchange='hub_removed', exchange_type='fanout')
    channel.queue_declare(queue='hub_removed_event')
    channel.queue_bind(exchange='hub_removed', queue='hub_removed_event')

    def callback(ch, method, properties, body):
        from app import db
        from app.models import Event
        from run import app

        hub_id = int(body)
        with app.app_context():
            Event.query.filter_by(hub_id=hub_id).delete()
            db.session.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='hub_removed_event', on_message_callback=callback)

    channel.start_consuming()

if __name__ == '__main__':
    main()
