import pika

def post_hub_removed(hub_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    channel.exchange_declare(exchange='hub_removed', exchange_type='fanout')
    channel.basic_publish(exchange='hub_removed', routing_key='', body=str(hub_id))
    connection.close()
