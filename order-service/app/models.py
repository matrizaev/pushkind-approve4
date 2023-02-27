import enum
from functools import reduce
from itertools import groupby, tee

from app import db
from sqlalchemy.sql import expression


def reduce_position_status(
    acc: dict[str, any], validator: dict[str, any]
) -> dict[str, any]:
    acc_product_id = acc.get("product_id")
    validator_product_id = validator.get("product_id")
    if acc_product_id == validator_product_id:
        return max(acc, validator, key=lambda x: x["timestamp"])
    elif not acc_product_id or validator_product_id == -1:
        return validator
    else:
        return acc


class OrderStatus(enum.IntEnum):
    new = 0
    not_approved = 1
    partly_approved = 2
    approved = 3
    modified = 4
    cancelled = 5

    def __str__(self):
        pretty = [
            "Новая",
            "Отклонена",
            "В работе",
            "Согласована",
            "Исправлена",
            "Аннулирована",
        ]
        return pretty[self.value]

    def color(self):
        colors = ["white", "danger", "warning", "success", "secondary", "danger"]
        return colors[self.value]

    def to_dict(self):
        return {"name": self.name, "pretty": str(self), "color": self.color()}


OrderRelationship = db.Table(
    "order_relationship",
    db.Model.metadata,
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("child_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    number = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    initiative = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    products = db.Column(db.JSON, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(
        db.Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.new,
        server_default="new",
    )
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    purchased = db.Column(
        db.Boolean, nullable=False, default=False, server_default=expression.false()
    )
    exported = db.Column(
        db.Boolean, nullable=False, default=False, server_default=expression.false()
    )
    dealdone = db.Column(
        db.Boolean, nullable=False, default=False, server_default=expression.false()
    )
    over_limit = db.Column(
        db.Boolean, nullable=False, default=False, server_default=expression.false()
    )
    dealdone_responsible = db.Column(db.String(128), nullable=True)
    dealdone_comment = db.Column(db.String(512), nullable=True)
    project = db.Column(db.String(128), nullable=True)
    site = db.Column(db.String(128), nullable=True)
    income = db.Column(db.String(128), nullable=True)
    cashflow = db.Column(db.String(128), nullable=True)
    budget_holder = db.Column(db.String(128), nullable=True)
    responsible = db.Column(db.JSON, nullable=True)
    positions = db.Column(db.JSON, nullable=True)

    purchasers = db.relationship(
        "OrderPurchaser",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
    )
    categories = db.relationship(
        "OrderCategory",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
    )
    vendors = db.relationship(
        "OrderVendor",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
    )
    validators = db.relationship(
        "OrderValidator",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
    )
    children = db.relationship(
        "Order",
        secondary=OrderRelationship,
        primaryjoin=id == OrderRelationship.c.order_id,
        secondaryjoin=id == OrderRelationship.c.child_id,
        viewonly=True,
    )
    parents = db.relationship(
        "Order",
        secondary=OrderRelationship,
        primaryjoin=id == OrderRelationship.c.child_id,
        secondaryjoin=id == OrderRelationship.c.order_id,
    )

    def to_dict(self, with_products=False):
        data = {
            "id": self.id,
            "number": self.number,
            "email": self.email,
            "initiative": self.initiative,
            "timestamp": self.timestamp.date().isoformat(),
            "total": self.total,
            "status": self.status.to_dict(),
            "project": self.project,
            "site": self.site,
            "income": self.income,
            "cashflow": self.cashflow,
            "purchased": self.purchased,
            "exported": self.exported,
            "dealdone": self.dealdone,
            "over_limit": self.over_limit,
            "dealdone_responsible": self.dealdone_responsible,
            "dealdone_comment": self.dealdone_comment,
            "categories": {c.name: c.code for c in self.categories},
            "vendors": [v.name for v in self.vendors],
            "positions": self.positions,
            "children": [(o.id, o.number) for o in self.children],
            "parents": [(o.id, o.number) for o in self.parents],
            "purchasers": [p.user for p in self.purchasers],
        }
        if with_products:
            data["products"] = self.products
        return data

    def from_dict(self, data):
        data.pop("id", None)
        data.pop("hub_id", None)
        data.pop("email", None)
        data.pop("initiative", None)
        data.pop("number", None)
        data.pop("status", None)
        data.pop("vendors", None)
        data.pop("purchasers", None)
        data.pop("approvals", None)

        data.pop("children", None)
        parents = data.pop("parents", [])
        products = data.pop("products", None)
        categories = data.pop("categories", None)
        responsibilities = data.pop("responsibilities", None)
        if products:
            self.products = products
            self.total = sum(p["price"] * p["quantity"] for p in products)
            self.vendors = [
                OrderVendor(order_id=self.id, email=k, name=v)
                for k, v in {
                    p["vendor"]["email"]: p["vendor"]["name"] for p in products
                }.items()
            ]
            self.categories = [
                OrderCategory(order_id=self.id, name=k, code=c)
                for k, c in {
                    p["category"]["name"]: p["category"]["code"] for p in products
                }.items()
            ]

        if categories:
            self.categories = [
                OrderCategory(order_id=self.id, name=k, code=c)
                for k, c in {p["name"]: p["code"] for p in categories}.items()
            ]

        if parents:
            self.parents = Order.query.filter(Order.id.in_(parents)).all()

        if responsibilities:
            self.purchasers = [
                OrderPurchaser(order_id=self.id, email=p["email"], user=p)
                for p in responsibilities["purchasers"]
            ]
            old_validators = {v.email: v for v in self.validators}
            self.validators = [
                OrderValidator(
                    order_id=self.id,
                    email=p["email"],
                    user=p,
                    position=p["position"],
                    product_id=old_validators.get(p["email"], {}).get("product_id"),
                    timestamp=old_validators.get(p["email"], {}).get("timestamp"),
                    remark=old_validators.get(p["email"], {}).get("remark"),
                )
                for p in responsibilities["validators"]
            ]
            self.positions = self.get_positions()

        for k, v in data.items():
            setattr(self, k, v)

    def get_positions(self):
        positions = {"approved": {}, "disapproved": {}, "waiting": {}}
        for position, group in groupby(self.validators, lambda x: x.position):
            iterators = tee(group, 2)
            position_status = reduce(reduce_position_status, iterators[0])
            if position_status.product_id is None:
                positions["waiting"][position] = [v.to_dict() for v in iterators[1]]
            elif position_status.product_id >= 0:
                positions["disapproved"][position] = position_status.to_dict()
            else:
                positions["approved"][position] = position_status.to_dict()
        return positions


class OrderValidator(db.Model):
    __tablename__ = "order_validator"
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    email = db.Column(db.String(128), primary_key=True)
    position = db.Column(db.String(128), nullable=False)
    # None no actions so far, -1 - approved the order, 0 - disapproved the order,
    # > 1 disapproved the product id
    product_id = db.Column(db.Integer, index=True, nullable=True, default=None)
    remark = db.Column(db.String(512), nullable=True)
    user = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "position": self.position,
            "product_id": self.product_id,
            "remark": self.remark,
            "user": self.user,
            "timestamp": self.timestamp.date().isoformat()
            if self.timestamp is not None
            else None,
        }


class OrderPurchaser(db.Model):
    __tablename__ = "order_purchaser"
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    email = db.Column(db.String(128), primary_key=True)
    user = db.Column(db.JSON, nullable=False)


class OrderVendor(db.Model):
    __tablename__ = "order_vendor"
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    email = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(128), nullable=False)


class OrderCategory(db.Model):
    __tablename__ = "order_category"
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), primary_key=True
    )
    name = db.Column(db.String(128), primary_key=True)
    code = db.Column(db.String(128), nullable=False)
