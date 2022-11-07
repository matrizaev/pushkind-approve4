from app.api.entity import EntityApi


EVENT_SERVICE_HOST = 'event-service:5000'

class EventApi(EntityApi):
    __entity_name__ = 'event'
    __entities_name__ = 'events'
    __service_host__ = EVENT_SERVICE_HOST


class EventTypeApi(EntityApi):
    __entity_name__ = 'event_type'
    __entities_name__ = 'event_types'
    __service_host__ = EVENT_SERVICE_HOST
