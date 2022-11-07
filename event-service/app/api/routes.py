from datetime import datetime, timezone
from flask import request, jsonify

from app import db
from app.api import bp
from app.models import Event, EventType, EventEntityType
from app.api.auth import token_auth
from app.api.errors import error_response


@bp.route('/events', methods=['GET'])
@token_auth.login_required
def get_events():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    timestamp = args.pop('timestamp', None)
    entity_type = args.pop('entity_type', None)
    event_type = args.pop('event_type', None)
    events = (
        Event
        .query
        .filter_by(hub_id=current_user.hub_id)
        .filter_by(**args)
    )
    if timestamp is not None:
        timestamp = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
        events = events.filter(Event.timestamp > timestamp)
    if entity_type is not None:
        try:
            entity_type = EventEntityType[entity_type]
        except KeyError:
            entity_type = EventEntityType.hub
        events = events.filter_by(entity_type=entity_type)
    if event_type is not None:
        try:
            event_type = EventType[event_type]
        except KeyError:
            event_type = EventType.commented
        events = events.filter_by(event_type=event_type)
    events = events.all()
    return jsonify([e.to_dict() for e in events]), 200


@bp.route('/event_types', methods=['GET'])
@token_auth.login_required
def get_event_types():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([i.to_dict() for i in EventType]), 200


@bp.route('/event', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_event():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('event_type') is None or data.get('data') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    event = Event(
        hub_id=current_user.hub_id,
        user_id=current_user.id,
        user={
            'name': current_user.name,
            'role': current_user.role,
            'email': current_user.email,
            'position': current_user.position,
            'location': current_user.location,
            'phone': current_user.phone
        }
    )
    event.from_dict(data)
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201
