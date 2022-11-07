import os

from app import create_app, db
from app.models import User, UserRoles, Position, UserCategory, UserProject


environment_configuration=os.environ['CONFIGURATION_SETUP']
app = create_app(environment_configuration)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'UserRoles': UserRoles,
        'Position': Position,
        'UserCategory': UserCategory,
        'UserProject': UserProject
    }
