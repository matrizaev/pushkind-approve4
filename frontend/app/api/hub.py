from app.api.entity import EntityApi


HUB_SERVICE_HOST = 'hub-service:5000'

class HubApi(EntityApi):
    __entity_name__ = 'hub'
    __entities_name__ = 'hubs'
    __service_host__ = HUB_SERVICE_HOST


class VendorApi(EntityApi):
    __entity_name__ = 'vendor'
    __entities_name__ = 'vendors'
    __service_host__ = HUB_SERVICE_HOST


class CategoryApi(EntityApi):
    __entity_name__ = 'category'
    __entities_name__ = 'categories'
    __service_host__ = HUB_SERVICE_HOST


class AppSettingsApi(EntityApi):
    __entity_name__ = 'app_settings'
    __entities_name__ = 'app_settings'
    __service_host__ = HUB_SERVICE_HOST


class ProductApi(EntityApi):
    __entity_name__ = 'product'
    __entities_name__ = 'products'
    __service_host__ = HUB_SERVICE_HOST
