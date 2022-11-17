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


def callback_hub_changed(ch, method, properties, body):
    import json
    from app import db
    from app.models import User, Position, UserRoles
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        if removed:
            User.query.filter(User.hub_id==hub_id, User.role != UserRoles.admin).delete()
            db.session.execute(update(User).where(User.hub_id==hub_id, User.role == UserRoles.admin).values(hub_id=None))
            Position.query.filter_by(hub_id=hub_id).delete()
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def callback_project_changed(ch, method, properties, body):
    import json
    from sqlalchemy import func
    from app import db
    from app.models import User, UserProject
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        renamed = data.get('renamed')
        if removed:
            projects = UserProject.query.filter(func.lower(UserProject.project)==removed.lower()).join(User).filter_by(hub_id=hub_id).all()
            for project in projects:
                db.session.delete(project)
        if renamed:
            projects = UserProject.query.filter(func.lower(UserProject.project)==renamed[0].lower()).join(User).filter_by(hub_id=hub_id).all()
            for project in projects:
                project.project = renamed[1]
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def callback_category_changed(ch, method, properties, body):
    import json
    from sqlalchemy import func
    from app import db
    from app.models import User, UserCategory
    from run import app

    data = json.loads(body)
    with app.app_context():
        hub_id = data.get('hub_id')
        removed = data.get('removed')
        renamed = data.get('renamed')
        if removed:
            categories = UserCategory.query.filter(func.lower(UserCategory.category)==removed.lower()).join(User).filter_by(hub_id=hub_id).all()
            for category in categories:
                db.session.delete(category)
        if renamed:
            category = UserCategory.query.filter(func.lower(UserCategory.category)==renamed[0].lower()).join(User).filter_by(hub_id=hub_id).all()
            for category in categories:
                category.category = renamed[1]
        db.session.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    wait_for_port_open('mq-service', 5672)
    logging.info('The RabbitMQ is available. Proceeding.')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()

    channel.exchange_declare(exchange='hub_changed', exchange_type='fanout')
    channel.queue_declare(queue='hub_changed_user')
    channel.queue_bind(exchange='hub_changed', queue='hub_changed_user')

    channel.exchange_declare(exchange='project_changed', exchange_type='fanout')
    channel.queue_declare(queue='project_changed_user')
    channel.queue_bind(exchange='project_changed', queue='project_changed_user')

    channel.exchange_declare(exchange='category_changed', exchange_type='fanout')
    channel.queue_declare(queue='category_changed_user')
    channel.queue_bind(exchange='category_changed', queue='category_changed_user')

    channel.basic_consume(queue='hub_changed_user', on_message_callback=callback_hub_changed)
    channel.basic_consume(queue='project_changed_user', on_message_callback=callback_project_changed)
    channel.basic_consume(queue='category_changed_user', on_message_callback=callback_category_changed)

    channel.start_consuming()

if __name__ == '__main__':
    main()
