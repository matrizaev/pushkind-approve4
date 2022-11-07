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
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    orders = (
        Order
        .query
        .filter_by(hub_id=current_user.hub_id)
        .filter_by(**request.args)
        .all()
    )
    return jsonify([o.to_dict() for o in orders]), 200


@bp.route('/order_statuses', methods=['GET'])
@token_auth.login_required
def get_order_statuses():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([status.to_dict() for status in OrderStatus]), 200
