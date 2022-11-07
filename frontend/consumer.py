import socket
import logging
import json
from time import sleep
from io import BytesIO
from base64 import b64decode
from pathlib import Path

from requests import get
import pandas as pd
import pika
from flask import current_app


logging.basicConfig(level=logging.INFO)


def download_image(vendor_id, static_path, sku, url):
    try:
        response = get(url)
    except:
        return
    if not response or response.status_code != 200:
        return
    if int(response.headers['content-length']) > current_app.config['MAX_FILE_SIZE']:
        return
    content_type = response.headers.get('content-type').lower()
    if 'image' not in content_type:
        return

    static_path = static_path / Path(sku)

    with open(static_path, 'wb') as f:
        f.write(response.content)



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
    channel.queue_declare(queue='frontend_upload_images')

    def callback(ch, method, properties, body):
        from run import app

        body = json.loads(body)
        with app.app_context():
            for vendor_id, data in body.items():
                static_path = Path(f'app/static/upload/vendor{vendor_id}')
                static_path.mkdir(parents=True, exist_ok=True)

                buf = BytesIO(b64decode(data.encode()))
                buf.seek(0)
                df = pd.read_excel(
                    buf,
                    engine='openpyxl'
                )
                df.columns = df.columns.str.lower()
                if 'image' not in df.columns:
                    continue
                df.drop(
                    df.columns.difference([
                        'sku',
                        'image'
                    ]),
                    axis=1,
                    inplace=True
                )
                df = df.astype(
                    dtype = {
                        'sku': str,
                        'image': str
                    }
                )

                for index, row in df.iterrows():
                    download_image(vendor_id, static_path, *row)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='frontend_upload_images', on_message_callback=callback)

    channel.start_consuming()

if __name__ == '__main__':
    main()
