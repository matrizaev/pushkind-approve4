import enum

from sqlalchemy.sql import expression

from app import db


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
        index=True
    )
    uid = db.Column(db.String(128), nullable=True)
    sites = db.relationship(
        'Site',
        cascade='all, delete, delete-orphan',
        back_populates='project',
        passive_deletes=True
    )
    order_limits = db.relationship(
        'OrderLimit',
        back_populates='project',
        cascade='all, delete, delete-orphan',
        passive_deletes=True
    )

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'uid': self.uid,
            'enabled': self.enabled,
            'sites': [site.to_dict() for site in self.sites]
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('sites', None)
        data.pop('order_limits', None)
        for key, value in data.items():
            setattr(self, key, value)


class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id', ondelete="CASCADE"),
        nullable=False
    )
    uid = db.Column(db.String(128), nullable=True)
    project = db.relationship('Project', back_populates='sites')

    def to_dict(self):
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'uid': self.uid
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('project_id', None)
        data.pop('project', None)
        for key, value in data.items():
            setattr(self, key, value)


class IncomeStatement(db.Model):
    __tablename__ = 'income_statement'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False, index=True)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        for key, value in data.items():
            setattr(self, key, value)


class CashflowStatement(db.Model):
    __tablename__ = 'cashflow_statement'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    order_limits = db.relationship(
        'OrderLimit',
        back_populates='cashflow_statement',
        cascade='all, delete, delete-orphan',
        passive_deletes=True
    )

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('order_limits', None)
        for key, value in data.items():
            setattr(self, key, value)


class BudgetHolder(db.Model):
    __tablename__ = 'budget_holder'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False, index=True)

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        for key, value in data.items():
            setattr(self, key, value)


class OrderLimitsIntervals(enum.IntEnum):
    daily = 0
    weekly = 1
    monthly = 2
    quarterly = 3
    annually = 4
    all_time = 5

    def __str__(self):
        pretty = [
            'День',
            'Неделя',
            'Месяц',
            'Квартал',
            'Год',
            'Всё время'
        ]
        return pretty[self.value]

    def to_dict(self):
        return {
            'name': self.name,
            'pretty': str(self)
        }


class OrderLimit(db.Model):
    __tablename__ = 'order_limit'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    value = db.Column(db.Float, nullable=False, default=0.0, server_default='0.0')
    current = db.Column(db.Float, nullable=False, default=0.0, server_default='0.0')
    cashflow_id = db.Column(
        db.Integer,
        db.ForeignKey('cashflow_statement.id', ondelete='CASCADE'),
        nullable=False
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id', ondelete='CASCADE'),
        nullable=False
    )
    interval = db.Column(
        db.Enum(OrderLimitsIntervals),
        index=True,
        nullable=False,
        default=OrderLimitsIntervals.monthly,
        server_default='monthly'
    )
    cashflow_statement = db.relationship('CashflowStatement', back_populates='order_limits')
    project = db.relationship('Project', back_populates='order_limits')

    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'current': self.current,
            'cashflow': self.cashflow_statement.name,
            'project': self.project.name,
            'interval': self.interval.to_dict()
        }

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('cashflow_id', None)
        data.pop('project_id', None)
        data.pop('cashflow_statement', None)
        data.pop('project', None)
        interval = data.pop('interval', self.interval.name if self.interval is not None else 'monthly')
        try:
            self.interval = OrderLimitsIntervals[interval]
        except KeyError:
            self.interval = OrderLimitsIntervals.monthly
        for key, value in data.items():
            setattr(self, key, value)
