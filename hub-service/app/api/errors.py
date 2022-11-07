from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException

from app.api import bp


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


@bp.app_errorhandler(HTTPException)
def http_error_handler(error):
    return error_response(error.code)
