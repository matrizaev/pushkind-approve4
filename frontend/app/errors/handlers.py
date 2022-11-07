from flask import render_template

from app.errors import bp


@bp.app_errorhandler(400)
@bp.app_errorhandler(403)
@bp.app_errorhandler(404)
@bp.app_errorhandler(413)
@bp.app_errorhandler(500)
@bp.app_errorhandler(503)
def http_error(error):
    return render_template(f'errors/{error.code}.html', error=error), error.code
