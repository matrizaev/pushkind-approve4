from app.api.entity import EntityApi


PROJECT_SERVICE_HOST = 'project-service:5000'

class ProjectApi(EntityApi):
    __entity_name__ = 'project'
    __entities_name__ = 'projects'
    __service_host__ = PROJECT_SERVICE_HOST


class SiteApi(EntityApi):
    __entity_name__ = 'site'
    __entities_name__ = 'sites'
    __service_host__ = PROJECT_SERVICE_HOST


class IncomeApi(EntityApi):
    __entity_name__ = 'income'
    __entities_name__ = 'incomes'
    __service_host__ = PROJECT_SERVICE_HOST


class CashflowApi(EntityApi):
    __entity_name__ = 'cashflow'
    __entities_name__ = 'cashflows'
    __service_host__ = PROJECT_SERVICE_HOST


class OrderLimitApi(EntityApi):
    __entity_name__ = 'order_limit'
    __entities_name__ = 'order_limits'
    __service_host__ = PROJECT_SERVICE_HOST


class OrderLimitIntervalApi(EntityApi):
    __entity_name__ = 'order_limit_interval'
    __entities_name__ = 'order_limit_intervals'
    __service_host__ = PROJECT_SERVICE_HOST


class BudgetHolderApi(EntityApi):
    __entity_name__ = 'budget_holder'
    __entities_name__ = 'budget_holders'
    __service_host__ = PROJECT_SERVICE_HOST
