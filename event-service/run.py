import os

from app import create_app


environment_configuration=os.environ['CONFIGURATION_SETUP']
app = create_app(environment_configuration)
