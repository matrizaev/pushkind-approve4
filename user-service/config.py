import os
from pathlib import Path
from dotenv import load_dotenv


basedir = Path(__file__).parent.resolve()
load_dotenv(basedir / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MYSQL_DATABASE_CHARSET = 'utf8mb4'
    MYSQL_CHARSET = 'utf8mb4'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_SENDERNAME=os.environ.get('MAIL_SENDERNAME') or 'Sender'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class DevelopmentConfig(Config):
    ENV='development'
    DEBUG=True
    SQLALCHEMY_ECHO=True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(basedir / 'app.db')


class ProductionConfig(Config):
    ENV='production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URL')
