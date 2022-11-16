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
    initiative_id = db.Column(db.Integer, nullable=False, index=True)
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
    dealdone_responsible = db.Column(db.JSON(), nullable=True)
    dealdone_comment = db.Column(db.String(512), nullable=True)
    project = db.Column(db.JSON(), nullable=True)
    site = db.Column(db.JSON(), nullable=True)
    income = db.Column(db.JSON(), nullable=True)
    cashflow = db.Column(db.JSON(), nullable=True)
    budget_holder = db.Column(db.JSON(), nullable=True)
    responsible = db.Column(db.JSON(), nullable=True)

    categories = db.relationship(
        'OrderCategory',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )
    vendors = db.relationship(
        'OrderVendor',
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
            'initiative': self.initiative,
            'timestamp': self.timestamp.isoformat(),
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
            'categories': [(c.category, c.code) for c in self.categories],
            'vendors': [v.vendor for v in self.vendors],
            'approvals': [a.to_dict() for a in self.approvals],
            'children': [(o.id, o.number) for o in self.children],
            'parents': [(o.id, o.number) for o in self.parents]
        }
        if with_products:
            data['products'] = self.products
        return data


    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('initiative_id', None)
        data.pop('initiative', None)
        data.pop('number', None)
        data.pop('categories', None)
        data.pop('vendors', None)
        data.pop('income', None)
        data.pop('cashflow', None)
        data.pop('budget_holder', None)
        data.pop('responsible', None)
        data.pop('status', None)

        data.pop('children', [])
        parents = data.pop('parents', [])
        products = data.pop('products', [])
        responsibilities = data.pop('responsibilities', {})
        if products:
            total = 0
            categories = {}
            vendors = set()
            income = None
            cashflow = None
            responsible = None
            budget_holder = None
            for product in products:
                total += product['price']*product['quantity']
                categories[product['category']['name']] = product['category']['code']
                vendors.add(product['vendor']['name'])
                income = product['category']['income'] if income is None else income
                cashflow = product['category']['cashflow'] if cashflow is None else cashflow
                budget_holder = product['category']['budget_holder'] if budget_holder is None else budget_holder
                responsible = product['category']['responsible'] if responsible is None else responsible
            self.responsible = responsible
            self.cashflow = cashflow
            self.responsible = responsible
            self.budget_holder = budget_holder
            self.vendors = [OrderVendor(order_id=self.id, vendor=v) for v in vendors]
            self.categories = [OrderCategory(order_id=self.id, category=k, code=c) for k, c in categories.items()]
            self.products = products
            self.total = total

        if parents:
            self.parents = Order.query.filter(Order.id.in_(parents)).all()

        if responsibilities:
            old_approvals = {
                appr.position:appr.to_dict() for appr in self.approvals
            }
            self.approvals = [OrderPosition(
                order_id=self.id,
                position=k,
                users=v,
                approved = old_approvals.get(k, {'approved': None})['approved'],
                timestamp = old_approvals.get(k, {'timestamp': None})['timestamp'],
                user = old_approvals.get(k, {'user': None})['user'],
            ) for k,v in responsibilities.items()]

        for k, v in data.items():
            setattr(self, k, v)



class OrderCategory(db.Model):
    __tablename__ = 'order_category'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), primary_key=True)
    category = db.Column(db.String(128), primary_key=True)
    code = db.Column(db.String(128))


class OrderVendor(db.Model):
    __tablename__ = 'order_vendor'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), primary_key=True)
    vendor = db.Column(db.String(128), primary_key=True)


class OrderPosition(db.Model):
    __tablename__ = 'order_position'
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), primary_key=True)
    position = db.Column(db.String(128), primary_key=True)
    users = db.Column(db.JSON(), nullable=False)
    approved = db.Column(db.Boolean, nullable=True)
    user = db.Column(db.JSON(), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'position': self.position,
            'users': self.users,
            'approved': self.approved,
            'user': self.user,
            'timestamp': self.timestamp.isoformat() if self.timestamp is not None else None
        }
