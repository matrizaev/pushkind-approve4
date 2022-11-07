import json

import pika

def post_upload_images(vendor_id, data):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    channel.queue_declare(queue="frontend_upload_images")
    channel.basic_publish(exchange='', routing_key='frontend_upload_images', body=json.dumps({vendor_id:data}))
    connection.close()


def get_upload_image_queue_size():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    queue = channel.queue_declare(queue="frontend_upload_images")
    result = queue.method.message_count
    connection.close()
    return result
