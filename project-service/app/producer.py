import pika

def post_income_removed(income_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    channel.exchange_declare(exchange='income_removed', exchange_type='fanout')
    channel.basic_publish(exchange='income_removed', routing_key='', body=str(income_id))
    connection.close()

def post_cashflow_removed(cashflow_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='mq-service'))
    channel = connection.channel()
    channel.exchange_declare(exchange='cashflow_removed', exchange_type='fanout')
    channel.basic_publish(exchange='cashflow_removed', routing_key='', body=str(cashflow_id))
    connection.close()
