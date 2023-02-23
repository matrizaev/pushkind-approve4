import click
from app import db
from app.models import User, UserRoles


def register(app):
    @app.cli.group()
    def bootstrap():
        pass

    @bootstrap.command()
    @click.argument('email')
    @click.argument('password')
    def init(email, password):
        admin = User(
            email=email,
            role=UserRoles.admin
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
