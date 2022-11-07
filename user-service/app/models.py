import enum
from time import time
from hashlib import md5

import jwt
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import expression

from app import db


class UserRoles(enum.IntEnum):
    default = 0
    admin = 1
    initiative = 2
    validator = 3
    purchaser = 4
    supervisor = 5
    vendor = 6

    def __str__(self):
        pretty = [
            'Без роли',
            'Администратор',
            'Инициатор',
            'Валидатор',
            'Закупщик',
            'Наблюдатель',
            'Поставщик'
        ]
        return pretty[self.value]

    def to_dict(self):
        return {
            'id': int(self),
            'name': self.name,
            'pretty': str(self)
        }


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.Enum(UserRoles),
        index=True,
        nullable=False,
        default=UserRoles.default,
        server_default='default'
    )
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(128), nullable=True)
    position_id = db.Column(
        db.Integer,
        db.ForeignKey('position.id', ondelete='SET NULL'),
        nullable=True
    )
    location = db.Column(db.String(512), nullable=True)
    hub_id = db.Column(
        db.Integer,
        nullable=True
    )
    email_new = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email_modified = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email_disapproved = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email_approved = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    email_comment = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    last_seen = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Text(), nullable=True)
    registered = db.Column(db.DateTime, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    position = db.relationship('Position', back_populates='users')
    categories = db.relationship('UserCategory', cascade="save-update, merge, delete, delete-orphan")
    projects = db.relationship('UserProject', cascade="save-update, merge, delete, delete-orphan")


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_token(self, expires_in=60):
        token = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'location': self.location,
            'position': self.position.name if self.position is not None else None,
            'role': self.role.to_dict(),
            'hub_id': self.hub_id,
            'exp': time() + expires_in
        }
        return jwt.encode(
            token,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_token(token, verify_exp=True):
        try:
            user_id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'],
                options={
                    'verify_exp':verify_exp
                }
            )['id']
        except:
            return None
        return User.query.get(user_id)

    def from_dict(self, data):
        data.pop('id', None)
        data.pop('last_seen', None)
        data.pop('registered', None)
        data.pop('hub_id', None)
        data.pop('email', None)
        password = data.pop('password', None)

        if password is not None:
            self.set_password(password)

        role = data.pop('role', self.role.name if self.role is not None else 'default')
        try:
            self.role = UserRoles[role]
        except KeyError:
            self.role = UserRoles.default

        projects = data.pop('projects', None)
        categories = data.pop('categories', None)
        if self.role in [UserRoles.validator, UserRoles.purchaser]:
            if projects is not None:
                self.projects = [UserProject(user_id=self.id, project_id=p) for p in projects]
            if categories is not None:
                self.categories = [UserCategory(user_id=self.id, category_id=c) for c in categories]
        else:
            self.projects = []
            self.categories = []

        position_name = data.pop('position', None)
        position_name = position_name.lower() if position_name is not None else None
        if position_name is not None and self.hub_id is not None:
            position = Position.query.filter_by(hub_id=self.hub_id, name=position_name).first()
            if position is None:
                position = Position(name=position_name, hub_id=self.hub_id)
            self.position = position

        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self):
        data = {
            'id': self.id,
            'email': self.email,
            'phone': self.phone if self.phone is not None else None,
            'note': self.note,
            'birthday': self.birthday.isoformat() if self.birthday is not None else None,
            'role': self.role.to_dict(),
            'position': self.position.name if self.position is not None else None,
            'name': self.name if self.name is not None else None,
            'location': self.location if self.location is not None else None,
            'email_new': self.email_new,
            'email_modified': self.email_modified,
            'email_disapproved': self.email_disapproved,
            'email_approved': self.email_approved,
            'email_comment': self.email_comment,
            'projects': [p.project_id for p in self.projects],
            'categories': [c.category_id for c in self.categories],
            'last_seen': self.last_seen.isoformat() if self.last_seen is not None else None,
            'registered': self.registered.isoformat() if self.registered is not None else None
        }
        return data


class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    hub_id = db.Column(db.Integer, nullable=False)
    users = db.relationship('User', back_populates='position')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'users': [u.to_dict() for u in self.users]
        }

    def __eq__(self, other):
        if not isinstance(other, Position) or self.id != other.id:
            return False
        return True

    @staticmethod
    def cleanup_unused():
        Position.query.filter(Position.users == None).delete(synchronize_session=False)

    @staticmethod
    def get_responsibility(hub_id, project_id, category_list):

        responsibility = {}
        users = (
            User.query.filter_by(hub_id=hub_id, role=UserRoles.validator)
            .filter(User.position != None)
            .join(UserCategory).filter(UserCategory.category_id.in_(category_list))
            .join(UserProject).filter(UserProject.project_id == project_id)
            .all()
        )
        for user in users:
            if user.position_id not in responsibility:
                responsibility[user.position_id] = {
                    'position': user.position.name,
                    'users': []
                }
            responsibility[user.position_id]['users'].append(user.to_dict())
        return responsibility


class UserCategory(db.Model):
    __tablename__ = 'user_category'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    category_id = db.Column(db.Integer, primary_key=True)

    @staticmethod
    def cleanup_unused():
        if current_app.config['SQLALCHEMY_DATABASE_URI'].lower().startswith('mysql'):
            db.session.execute(
                'DELETE user_category FROM user_category INNER JOIN user ON user.id = user_category.user_id WHERE user.role NOT IN ("validator", "purchaser")',
            )
        else:
            db.session.execute(
                'DELETE FROM user_category WHERE ROWID IN (SELECT user_category.ROWID FROM user_category INNER JOIN user ON user.id = user_category.user_id WHERE user.role NOT IN ("validator", "purchaser"))',
            )


class UserProject(db.Model):
    __tablename__ = 'user_project'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    project_id = db.Column(db.Integer, primary_key=True)

    @staticmethod
    def cleanup_unused():
        if current_app.config['SQLALCHEMY_DATABASE_URI'].lower().startswith('mysql'):
            db.session.execute(
                'DELETE user_project FROM user_project INNER JOIN user ON user.id = user_project.user_id WHERE user.role NOT IN ("validator", "purchaser")',
            )
        else:
            db.session.execute(
                'DELETE FROM user_project WHERE ROWID IN (SELECT user_project.ROWID FROM user_project INNER JOIN user ON user.id = user_project.user_id WHERE user.role NOT IN ("validator", "purchaser"))',
            )
