from pathlib import Path

from config import Config
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.event import listen

db = SQLAlchemy()

mail = Mail()
migrate = Migrate()

DB_COLLATE = "ru_RU.UTF-8"


def load_extension_path(path):
    def load_extension(dbapi_conn, _):
        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(path)
        dbapi_conn.enable_load_extension(False)
        dbapi_conn.execute("SELECT icu_load_collation(?, 'ICU_EXT_1')", (DB_COLLATE,))

    return load_extension


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    if (
        "ICU_EXTENSION_PATH" in app.config
        and Path(app.config["ICU_EXTENSION_PATH"]).exists()
    ):
        with app.app_context():
            listen(
                db.engine,
                "connect",
                load_extension_path(app.config["ICU_EXTENSION_PATH"]),
            )

    return app


from app import models
