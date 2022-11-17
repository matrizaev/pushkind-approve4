from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.api import bp
from app.models import Order, OrderStatus
from app.api.auth import token_auth
from app.api.errors import error_response


@bp.route('/orders', methods=['GET'])
@token_auth.login_required
def get_orders():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    with_products = args.pop('with_products', False)
    filters = args.pop('filters', None)
    orders = (
        Order
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
        .order_by(Order.timestamp.desc())
        .all()
    )
    return jsonify([o.to_dict(bool(with_products)) for o in orders]), 200


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
    order = Order(
        hub_id=current_user['hub_id'],
        initiative_id=current_user['id'],
        initiative=current_user,
        number = orders_count + data.pop('order_id_bias', 0) + 1,
        timestamp = datetime.now(tz=timezone.utc),
        status=OrderStatus.new,
        total=0.0,
        products=data.get('products', [])
    )
    db.session.add(order)
    db.session.commit()

    order.from_dict(data)
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
