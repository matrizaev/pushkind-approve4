import socket
import logging
from time import sleep

from sqlalchemy import update
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

    channel.exchange_declare(exchange='income_removed', exchange_type='fanout')
    channel.queue_declare(queue='income_removed_hub')
    channel.queue_bind(exchange='income_removed', queue='income_removed_hub')

    channel.exchange_declare(exchange='cashflow_removed', exchange_type='fanout')
    channel.queue_declare(queue='cashflow_removed_hub')
    channel.queue_bind(exchange='cashflow_removed', queue='cashflow_removed_hub')

    def callback_income(ch, method, properties, body):
        from app import db
        from app.models import Category
        from run import app

        income_id = int(body)
        with app.app_context():
            db.session.execute(update(Category).where(Category.income_id==income_id).values(income_id=None))
            db.session.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback_cashflow(ch, method, properties, body):
        from app import db
        from app.models import Category
        from run import app

        cashflow_id = int(body)
        with app.app_context():
            db.session.execute(update(Category).where(Category.cashflow_id==cashflow_id).values(cashflow_id=None))
            db.session.commit()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='income_removed_hub', on_message_callback=callback_income)
    channel.basic_consume(queue='cashflow_removed_hub', on_message_callback=callback_cashflow)

    channel.start_consuming()

if __name__ == '__main__':
    main()
