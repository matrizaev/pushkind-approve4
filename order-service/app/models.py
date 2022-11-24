import enum

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.sql import expression

from app import db


class OrderStatus(enum.IntEnum):
    new = 0
    not_approved = 1
    partly_approved = 2
    approved = 3
    modified = 4
    cancelled = 5

    def __str__(self):
        pretty = [
            'Новая',
            'Отклонена',
            'В работе',
            'Согласована',
            'Исправлена',
            'Аннулирована'
        ]
        return pretty[self.value]

    def color(self):
        colors = [
            'white',
            'danger',
            'warning',
            'success',
            'secondary',
            'danger'
        ]
        return colors[self.value]

    def to_dict(self):
        return {
            'name': self.name,
            'pretty': str(self),
            'color': self.color()
        }


OrderRelationship = db.Table(
    'order_relationship',
    db.Model.metadata,
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('child_id', db.Integer, db.ForeignKey('order.id'), primary_key=True)
)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    number = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    initiative = db.Column(db.JSON(), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    products = db.Column(db.JSON(), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(
        db.Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.new,
        server_default='new'
    )
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    purchased = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    exported = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    dealdone = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    over_limit = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    dealdone_responsible = db.Column(db.String(128), nullable=True)
    dealdone_comment = db.Column(db.String(512), nullable=True)
    project = db.Column(db.String(128), nullable=True)
    site = db.Column(db.String(128), nullable=True)
    income = db.Column(db.String(128), nullable=True)
    cashflow = db.Column(db.String(128), nullable=True)
    budget_holder = db.Column(db.String(128), nullable=True)
    responsible = db.Column(db.JSON(), nullable=True)

    purchasers = db.relationship(
        'OrderPurchaser',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )
    approvals = db.relationship(
        'OrderPosition',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )
    children = db.relationship(
        'Order',
        secondary=OrderRelationship,
        primaryjoin=id == OrderRelationship.c.order_id,
        secondaryjoin=id == OrderRelationship.c.child_id,
        viewonly=True
    )
    parents = db.relationship(
        'Order',
        secondary=OrderRelationship,
        primaryjoin=id == OrderRelationship.c.child_id,
        secondaryjoin=id == OrderRelationship.c.order_id
    )

    def to_dict(self, with_products=False):
        data = {
            'id': self.id,
            'number': self.number,
            'email': self.email,
            'initiative': self.initiative,
            'timestamp': self.timestamp.date().isoformat(),
            'total': self.total,
            'status': self.status.to_dict(),
            'project': self.project,
            'site': self.site,
            'income': self.income,
            'cashflow': self.cashflow,
            'purchased': self.purchased,
            'exported': self.exported,
            'dealdone': self.dealdone,
            'over_limit': self.over_limit,
            'dealdone_responsible': self.dealdone_responsible,
            'dealdone_comment': self.dealdone_comment,
            'categories': {p['category']['name']:p['category']['code'] for p in self.products},
            'vendors': list(set(p['vendor']['name'] for p in self.products)),
            'approvals': [a.to_dict() for a in self.approvals],
            'children': [(o.id, o.number) for o in self.children],
            'parents': [(o.id, o.number) for o in self.parents],
            'purchasers': [p.user for p in self.purchasers]
        }
        if with_products:
            data['products'] = self.products
        return data


    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('email', None)
        data.pop('number', None)
        data.pop('status', None)

        data.pop('children', None)
        parents = data.pop('parents', [])
        products = data.pop('products', None)
        responsibilities = data.pop('responsibilities', None)
        if products:
            self.products = products
            self.total = sum(p['price']*p['quantity'] for p in products)

        if parents:
            self.parents = Order.query.filter(Order.id.in_(parents)).all()

        if responsibilities:
            self.purchasers = [
                OrderPurchaser(
                    order_id=self.id,
                    email=p['email'],
                    user=p
                )
                for p in responsibilities['purchasers']
            ]
            old_approvals = {
                appr.position:appr.to_dict() for appr in self.approvals
            }
            self.approvals = [OrderPosition(
                order_id=self.id,
                position=k,
                validators=[
                    OrderPositionValidator(
                        order_id=self.id,
                        position=k,
                        email=u['email'],
                        user=u
                    )
                    for u in v
                ],
                approved = old_approvals.get(k, {'approved': None})['approved'],
                timestamp = old_approvals.get(k, {'timestamp': None})['timestamp'],
                email = old_approvals.get(k, {'email': None})['email'],
                user =  old_approvals.get(k, {'user': None})['user'],
            ) for k,v in responsibilities['validators'].items()]

        for k, v in data.items():
            setattr(self, k, v)


class OrderPosition(db.Model):
    __tablename__ = 'order_position'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), primary_key=True)
    position = db.Column(db.String(128), primary_key=True)
    approved = db.Column(db.Boolean, nullable=True)
    email = db.Column(db.String(128), nullable=True)
    user = db.Column(db.JSON(), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    validators = db.relationship(
        'OrderPositionValidator',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            'position': self.position,
            'validators': [v.user for v in self.validators],
            'approved': self.approved,
            'user': self.user,
            'timestamp': self.timestamp.date().isoformat() if self.timestamp is not None else None
        }


class OrderPositionValidator(db.Model):
    __tablename__ = 'order_position_validator'
    order_id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(128), primary_key=True)
    email = db.Column(db.String(128), nullable=False)
    user = db.Column(db.JSON(), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ['order_id', 'position'],
            [OrderPosition.order_id, OrderPosition.position]
        ),
        {}
    )


class OrderPurchaser(db.Model):
    __tablename__ = 'order_purchaser'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), primary_key=True)
    email = db.Column(db.String(128), primary_key=True)
    user = db.Column(db.JSON(), nullable=False)
