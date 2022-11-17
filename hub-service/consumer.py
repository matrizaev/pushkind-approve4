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


def callback_income_changed(ch, method, properties, body):
    import json
    from sqlalchemy import func
    from app import db
    from app.models import Category
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        renamed = data.get('renamed')
        if removed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.income)==removed.lower()).all()
            for category in categories:
                category.income = None
        if renamed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.income)==renamed[0].lower()).all()
            for category in categories:
                category.income = renamed[1]
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def callback_cashflow_changed(ch, method, properties, body):
    import json
    from sqlalchemy import func
    from app import db
    from app.models import Category
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        renamed = data.get('renamed')
        if removed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.cashflow)==removed.lower()).all()
            for category in categories:
                category.cashflow = None
        if renamed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.cashflow)==renamed[0].lower()).all()
            for category in categories:
                category.cashflow = renamed[1]
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def callback_budget_holder_changed(ch, method, properties, body):
    import json
    from sqlalchemy import func
    from app import db
    from app.models import Category
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        renamed = data.get('renamed')
        if removed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.budget_holder)==removed.lower()).all()
            for category in categories:
                category.budget_holder = None
        if renamed:
            categories = Category.query.filter_by(hub_id=hub_id).filter(func.lower(Category.budget_holder)==renamed[0].lower()).all()
            for category in categories:
                category.budget_holder = renamed[1]
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    wait_for_port_open('mq-service', 5672)
    logging.info('The RabbitMQ is available. Proceeding.')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()

    channel.exchange_declare(exchange='income_changed', exchange_type='fanout')
    channel.queue_declare(queue='income_changed_hub')
    channel.queue_bind(exchange='income_changed', queue='income_changed_hub')

    channel.exchange_declare(exchange='cashflow_changed', exchange_type='fanout')
    channel.queue_declare(queue='cashflow_changed_hub')
    channel.queue_bind(exchange='cashflow_changed', queue='cashflow_changed_hub')

    channel.exchange_declare(exchange='budget_holder_changed', exchange_type='fanout')
    channel.queue_declare(queue='budget_holder_changed_hub')
    channel.queue_bind(exchange='budget_holder_changed', queue='budget_holder_changed_hub')

    channel.basic_consume(queue='income_changed_hub', on_message_callback=callback_income_changed)
    channel.basic_consume(queue='cashflow_changed_hub', on_message_callback=callback_cashflow_changed)
    channel.basic_consume(queue='budget_holder_changed_hub', on_message_callback=callback_budget_holder_changed)

    channel.start_consuming()

if __name__ == '__main__':
    main()
