from datetime import datetime, timezone

from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response
from app.models import Order, OrderPurchaser, OrderStatus, OrderValidator, OrderVendor
from flask import jsonify, request


@bp.route('/orders', methods=['GET'])
@token_auth.login_required
def get_orders():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    timestamp = args.pop('timestamp', None)
    disapproved = args.pop('disapproved', None)
    orders = (
        Order
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
    )
    if disapproved is None:
        orders = orders.filter(
            ~Order.status.in_([OrderStatus.not_approved, OrderStatus.cancelled])
        )
    if timestamp is not None:
        orders = orders.filter(Order.timestamp > datetime.fromtimestamp(float(timestamp), tz=timezone.utc))
    if current_user['role']['name'] == 'initiative':
        orders = orders.filter(Order.email == current_user['email'])
    elif current_user['role']['name'] == 'purchaser':
        orders = orders.join(OrderPurchaser).filter(OrderPurchaser.email == current_user['email'])
    elif current_user['role']['name'] == 'validator':
        orders = orders.join(OrderValidator).filter(OrderValidator.email == current_user['email'])
    elif current_user['role']['name'] == 'vendor':
        orders = orders.join(OrderVendor).filter(OrderVendor.email == current_user['email'])
    orders = orders.order_by(Order.timestamp.desc()).all()
    return jsonify([o.to_dict('id' in args) for o in orders]), 200


@bp.route('/order_statuses', methods=['GET'])
@token_auth.login_required
def get_order_statuses():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([status.to_dict() for status in OrderStatus]), 200


@bp.route('/order', methods=['POST'])
@token_auth.login_required(role=['admin', 'purchaser', 'initiative'])
def post_order():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    orders_count = db.session.query(Order.id).count()
    data = request.json or {}
    if not all([data.get(key) is not None for key in ('products',)]):
        return error_response(400, 'Необходимые поля отсутствуют.')
    order = Order(
        hub_id=current_user['hub_id'],
        email=current_user['email'],
        initiative=current_user,
        number = orders_count + data.pop('order_id_bias', 0) + 1,
        timestamp = datetime.now(tz=timezone.utc),
        status=OrderStatus.new,
        total=sum(p['price']*p['quantity'] for p in data.get('products', [])),
        products=data.get('products', [])
    )
    db.session.add(order)
    db.session.commit()

    order.from_dict(data)
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
