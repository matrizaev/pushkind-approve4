import enum

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
            'id': int(self),
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
    initiative_id = db.Column(db.Integer, nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    products = db.Column(db.JSON(), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(
        db.Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.new,
        server_default='new'
    )
    site_id = db.Column(db.Integer, nullable=True, index=True)
    income_id = db.Column(  # БДР
        db.Integer,
        nullable=True,
        index=True
    )
    cashflow_id = db.Column(  # БДДС
        db.Integer,
        nullable=True,
        index=True
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
    dealdone_responsible_name = db.Column(db.String(128))
    dealdone_responsible_comment = db.Column(db.String(128))
    categories = db.relationship('OrderCategory')
    vendors = db.relationship('OrderVendor')
    approvals = db.relationship('OrderPosition')
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

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'initiative_id': self.initiative_id,
            'timestamp': self.timestamp.isoformat(),
            'products': self.products,
            'total': self.total,
            'status': self.status.to_dict(),
            'site_id': self.site_id,
            'income_id': self.income_id,
            'cashflow_id': self.cashflow_id,
            'purchased': self.purchased,
            'exported': self.exported,
            'dealdone': self.dealdone,
            'over_limit': self.over_limit,
            'dealdone_responsible_name': self.dealdone_responsible_name,
            'dealdone_responsible_comment': self.dealdone_responsible_comment,
            'categories': [c.category_id for c in self.categories],
            'vendors': [v.vendor_id for v in self.vendors],
            'approvals': [a.to_dict() for a in self.approvals],
            'children': [(o.id, o.number) for o in self.children],
            'parents': [(o.id, o.number) for o in self.parents]
        }


class OrderCategory(db.Model):
    __tablename__ = 'order_category'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    category_id = db.Column(db.Integer, primary_key=True)


class OrderVendor(db.Model):
    __tablename__ = 'order_vendor'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    vendor_id = db.Column(db.Integer, primary_key=True)


class OrderPosition(db.Model):
    __tablename__ = 'order_position'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    position_id = db.Column(db.Integer, primary_key=True)
    approved = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    user_id = db.Column(db.Integer, nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'position_id': self.position_id,
            'approved': self.approved,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat()
        }
