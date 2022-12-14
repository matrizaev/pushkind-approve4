from datetime import datetime, timezone

from flask import request, jsonify
from sqlalchemy import func

from app import db
from app.api import bp
from app.models import Order, OrderStatus, OrderPosition, OrderPurchaser, OrderPositionValidator
from app.api.auth import token_auth
from app.api.errors import error_response


@bp.route('/orders', methods=['GET'])
@token_auth.login_required
def get_orders():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    filters = args.pop('filters', {})
    orders = (
        Order
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
    )
    # if not filters.get('disapproved', None):
    #     orders = orders.filter(
    #         ~Order.status.in_([OrderStatus.not_approved, OrderStatus.cancelled])
    #     )
    # if filters.get('from', 0) > 0:
    #     orders = orders.filter(Order.timestamp > datetime.fromtimestamp(filters['from'], tz=timezone.utc))
    if current_user['role']['name'] == 'initiative':
        orders = orders.filter(Order.email == current_user['email'])
    elif current_user['role']['name'] == 'purchaser':
        orders = orders.join(OrderPurchaser).filter(OrderPurchaser.email == current_user['email'])
    elif current_user['role']['name'] == 'validator':
        orders = orders.join(OrderPositionValidator).filter(OrderPositionValidator.email == current_user['email'])
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
    print(order.to_dict())
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
