from datetime import datetime, timezone

from flask import request, jsonify
from sqlalchemy import or_

from app import db
from app.api import bp
from app.api.errors import error_response
from app.models import User, UserCategory, UserProject, UserRoles, Position
from app.api.auth import token_auth, multi_auth


@bp.route('/token', methods=['GET'])
@multi_auth.login_required
def get_token():
    token = multi_auth.current_user().get_token()
    multi_auth.last_seen = datetime.now(tz=timezone.utc)
    db.session.commit()
    return jsonify({'token': token})


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    users = User.query
    if current_user.role == UserRoles.admin:
        users = users.filter(or_(User.hub_id == current_user.hub_id, User.hub_id == None))
    else:
        users = users.filter_by(hub_id=current_user.hub_id)
    users = users.filter_by(**request.args).order_by(User.name).all()
    return jsonify([u.to_dict() for u in users]), 200


@bp.route('/user/<int:user_id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(user_id):
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    if current_user.role != UserRoles.admin:
        user_id = current_user.id
    user = (
        User
        .query
        .filter(or_(User.hub_id == current_user.hub_id, User.hub_id == None))
        .filter_by(id=user_id)
        .first()
    )
    if user is not None:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    else:
        return error_response(404, 'Пользователь не существует.')


@bp.route('/roles', methods=['GET'])
@token_auth.login_required
def get_roles():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([role.to_dict() for role in UserRoles]), 200


@bp.route('/positions', methods=['GET'])
@token_auth.login_required
def get_positions():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    positions = Position.query.filter_by(hub_id=current_user.hub_id).all()
    return jsonify([pos.to_dict() for pos in positions]), 200


@bp.route('/responsibilities', methods=['GET'])
@token_auth.login_required
def get_responsibilities():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    categories = request.args.getlist('categories')
    project = request.args.get('project', None)
    positions = Position.get_responsibility(current_user.hub_id, project, categories)
    return jsonify(positions), 200


@bp.route('/user', methods=['POST'])
def post_user():
    data = request.get_json() or {}
    if data.get('email') is None or data.get('password') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    email = str(data['email']).lower()
    user = User.query.filter_by(email=email).first()
    if user is not None:
        return error_response(409, 'Адрес электронной почты занят.')
    user = User(email=email, registered=datetime.now(tz=timezone.utc))
    user.from_dict(data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@bp.route('/user/<int:user_id>', methods=['PUT'])
@token_auth.login_required
def put_user(user_id):
    current_user = token_auth.current_user()
    data = request.get_json() or {}
    if current_user.hub_id is None and data.get('hub_id') is None:
        return error_response(404, 'Хаб не существует.')
    if current_user.role != UserRoles.admin:
        user_id = current_user.id
        data.pop('role', None)
    user = User.query.filter_by(id=user_id).filter(or_(User.hub_id==current_user.hub_id, User.hub_id==None)).first()
    if user is None:
        return error_response(404, 'Пользователь не существует.')
    if current_user.role in (UserRoles.admin, UserRoles.supervisor):
        user.hub_id = data.get('hub_id', current_user.hub_id)
    user.from_dict(data)
    db.session.commit()
    Position.cleanup_unused()
    UserCategory.cleanup_unused()
    UserProject.cleanup_unused()
    db.session.commit()
    return jsonify(user.to_dict()), 200
