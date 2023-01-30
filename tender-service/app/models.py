import enum

from app import db


class TenderStatus(enum.IntEnum):
    new = 0
    in_progress = 1
    finished = 2
    cancelled = 5

    def __str__(self):
        pretty = [
            'Новый',
            'В работе',
            'Завершен',
            'Аннулирован'
        ]
        return pretty[self.value]

    @property
    def color(self):
        colors = [
            'secondary',
            'warning',
            'success',
            'danger'
        ]
        return colors[self.value]

    def to_dict(self):
        return {
            'name': self.name,
            'pretty': str(self),
            'color': self.color
        }


class Tender(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    initiative_id = db.Column(db.Integer, nullable=False, index=True)
    initiative = db.Column(db.JSON(), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    products = db.Column(db.JSON(), nullable=False)
    status = db.Column(
        db.Enum(TenderStatus),
        nullable=False,
        default=TenderStatus.new,
        server_default='new'
    )
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    vendors = db.relationship(
        'TenderVendor',
        cascade='all, delete, delete-orphan',
        passive_deletes=True
    )

    def to_dict(self, vendor_id=None):
        data = {
            'id': self.id,
            'initiative': self.initiative,
            'timestamp': self.timestamp.date().isoformat(),
            'status': self.status.to_dict(),
            'vendors': [v.to_dict(vendor_id==v.vendor_id) for v in self.vendors]
        }
        if vendor_id is not None:
            data['products'] = self.products
        return data


class TenderVendor(db.Model):
    __tablename__ = 'tender_vendor'
    tender_id = db.Column(db.Integer, db.ForeignKey('tender.id', ondelete="CASCADE"), primary_key=True)
    vendor_id = db.Column(db.String(128), primary_key=True)
    products = db.Column(db.JSON(), nullable=False, default=[])
    delivery_all = db.Column(db.Boolean, nullable=False, default=True)
    delivery_type =  db.Column(db.String(128))
    shipment_days =  db.Column(db.Integer)
    delivery_distance = db.Column(db.Integer)
    payment_type = db.Column(db.String(128))

    def to_dict(self, include_products=False):
        data = {
            'vendor_id': self.vendor_id,
            'vendor': self.vendor
        }
        if include_products:
            data['products'] = self.products
        return data
