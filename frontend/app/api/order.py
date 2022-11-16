from app.api.entity import EntityApi


ORDER_SERVICE_HOST = 'order-service:5000'


class OrderApi(EntityApi):
    __entity_name__ = 'order'
    __entities_name__ = 'orders'
    __service_host__ = ORDER_SERVICE_HOST


class OrderStatusApi(EntityApi):
    __entity_name__ = 'order_status'
    __entities_name__ = 'order_statuses'
    __service_host__ = ORDER_SERVICE_HOST
