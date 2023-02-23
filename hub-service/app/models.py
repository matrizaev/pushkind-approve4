from app import db
from sqlalchemy.sql import expression


class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    hub_id = db.Column(
        db.Integer,
        db.ForeignKey('vendor.id', ondelete="CASCADE"),
        nullable=True
    )
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True, index=True)
    enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    vendors = db.relationship(
        'Vendor',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )
    products = db.relationship(
        'Product',
        back_populates='vendor',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )
    settings = db.relationship(
        'AppSettings',
        back_populates='hub',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'enabled': self.enabled,
        }

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('vendors', None)
        data.pop('products', None)
        data.pop('settings', None)
        data.pop('email', None)
        for key, value in data.items():
            setattr(self, key, value)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    responsible = db.Column(db.JSON(), nullable=True)
    budget_holder = db.Column(db.String(128), nullable=True)
    income = db.Column(db.String(128), nullable=True)
    cashflow = db.Column(db.String(128), nullable=True)
    code = db.Column(db.String(128), nullable=True)
    image = db.Column(db.String(128), nullable=True)
    products = db.relationship(
        'Product',
        back_populates='category',
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self, with_products=True):
        data = {
            'id': self.id,
            'name': self.name,
            'responsible': self.responsible,
            'budget_holder': self.budget_holder,
            'income': self.income,
            'cashflow': self.cashflow,
            'code': self.code,
            'image': self.image
        }
        if with_products:
            data['products'] = [p.to_dict() for p in self.products]
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('products', None)
        for key, value in data.items():
            setattr(self, key, value)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    vendor_id = db.Column(
        db.Integer,
        db.ForeignKey('vendor.id', ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(128), nullable=False, index=True)
    sku = db.Column(db.String(128), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(128), nullable=True)
    measurement = db.Column(db.String(128), nullable=True)
    cat_id = db.Column(
        db.Integer,
        db.ForeignKey('category.id', ondelete="CASCADE"),
        nullable=False
    )
    description = db.Column(db.String(512), nullable=True)
    input_required =  db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    options = db.Column(db.JSON(), nullable=True)
    category = db.relationship('Category', back_populates='products')
    vendor = db.relationship('Vendor', back_populates='products')

    def to_dict(self):
        data = {
            'id': self.id,
            'vendor': {
                'name': self.vendor.name,
                'email': self.vendor.email
            },
            'name': self.name,
            'sku': self.sku,
            'price': self.price,
            'image': self.image,
            'measurement': self.measurement,
            'description': self.description,
            'input_required': self.input_required,
            'options': self.options,
            'category': {
                'name': self.category.name,
                'code': self.category.code
            }
        }
        return data

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('vendor_id', None)
        data.pop('cat_id', None)
        data.pop('category', None)
        data.pop('vendor', None)
        for key, value in data.items():
            setattr(self, key, value)


class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    hub_id = db.Column(
        db.Integer,
        db.ForeignKey('vendor.id', ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    notify_1C = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email_1C = db.Column(db.String(128), nullable=True)
    order_id_bias = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default='0'
    )
    single_category_orders = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    hub = db.relationship('Vendor', back_populates='settings')

    def to_dict(self):
        return {
            'notify_1C': self.notify_1C,
            'email_1C': self.email_1C,
            'order_id_bias': self.order_id_bias,
            'single_category_orders': self.single_category_orders
        }

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('hub', None)
        for key, value in data.items():
            setattr(self, key, value)
