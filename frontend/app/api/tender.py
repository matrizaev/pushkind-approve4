from app.api.entity import EntityApi


EVENT_SERVICE_HOST = 'tender-service:5000'

class TenderApi(EntityApi):
    __entity_name__ = 'tender'
    __entities_name__ = 'tenders'
    __service_host__ = EVENT_SERVICE_HOST


class TenderStatusApi(EntityApi):
    __entity_name__ = 'tender_status'
    __entities_name__ = 'tender_statuses'
    __service_host__ = EVENT_SERVICE_HOST
