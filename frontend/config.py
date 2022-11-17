import os
from pathlib import Path
from dotenv import load_dotenv


basedir = Path(__file__).parent.resolve()
load_dotenv(basedir / '.env')

class Config:
    APPLICATION_TITLE = os.environ.get('APPLICATION_TITLE') or ''
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_SENDERNAME=os.environ.get('MAIL_SENDERNAME') or 'Sender'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    PLACEHOLDER_IMAGE = '/static/placeholder.png'
    MAX_FILE_SIZE=1600000


class DevelopmentConfig(Config):
    ENV='development'
    DEBUG=True


class ProductionConfig(Config):
    ENV='production'
