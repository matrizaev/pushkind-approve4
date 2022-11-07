from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes_index
from app.main import routes_approve
from app.main import routes_settings
from app.main import routes_help
from app.main import routes_history
from app.main import routes_admin
from app.main import routes_limits
from app.main import routes_shop
from app.main import routes_products
from app.main import routes_tenders
