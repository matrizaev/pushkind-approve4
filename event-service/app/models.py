import enum

from datetime import datetime, timezone

from app import db


class EventType(enum.IntEnum):
    commented = 0
    approved = 1
    disapproved = 2
    quantity = 3
    duplicated = 4
    purchased = 5
    exported = 6
    merged = 7
    dealdone = 8
    income_statement = 9
    cashflow_statement = 10
    site = 11
    measurement = 12
    splitted = 13
    project = 14
    notification = 15
    cancelled = 16
    invited = 17

    def __str__(self):
        pretty = [
            'комментарий',
            'согласование',
            'замечание',
            'изменение',
            'клонирование',
            'отправлено поставщику',
            'экспорт в 1С',
            'объединение',
            'законтрактовано',
            'изменение',
            'изменение',
            'изменение',
            'изменение',
            'разделение',
            'изменение',
            'уведомление',
            'аннулирована',
            'приглашение'
        ]
        return pretty[self.value]

    @property
    def color(self):
        colors = [
            'warning',
            'success',
            'danger',
            'primary',
            'dark',
            'dark',
            'dark',
            'dark',
            'dark',
            'primary',
            'primary',
            'primary',
            'primary',
            'dark',
            'primary',
            'dark',
            'danger',
            'primary'
        ]
        return colors[self.value]

    def to_dict(self):
        return {
            'id': int(self),
            'name': self.name,
            'pretty': str(self),
            'color': self.color
        }


class EventEntityType(enum.IntEnum):
    hub = 0
    order = 1
    tender = 2

    def __str__(self):
        pretty = [
            'хаб',
            'заявка',
            'тендер'
        ]
        return pretty[self.value]

    def to_dict(self):
        return {
            'id': int(self),
            'name': self.name,
            'pretty': str(self)
        }


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    hub_id = db.Column(db.Integer, nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    user = db.Column(db.JSON(), nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(tz=timezone.utc)
    )
    event_type = db.Column(db.Enum(EventType), nullable=False, default=EventType.commented)
    entity_type = db.Column(db.Enum(EventEntityType), nullable=False, default=EventEntityType.hub)
    data = db.Column(db.String(512), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'entity_id': self.entity_id,
            'user': self.user,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.to_dict(),
            'entity_type': self.entity_type.to_dict(),
            'data': self.data
        }

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('hub_id', None)
        data.pop('user_id', None)
        data.pop('user', None)
        event_type = data.pop('event_type', 'commented')
        try:
            self.event_type = EventType[event_type]
        except KeyError:
            self.event_type = EventType.commented

        entity_type = data.pop('entity_type', 'hub')
        try:
            self.entity_type = EventEntityType[entity_type]
        except KeyError:
            self.entity_type = EventEntityType.hub

        for key, value in data.items():
            setattr(self, key, value)
