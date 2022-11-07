from flask import render_template, request
from flask_login import login_required

from app.main import bp
from app.utils import role_forbidden
from app.utils import get_filter_timestamps
from app.api.event import EventApi


################################################################################
# Responibility page
################################################################################

@bp.route('/history/', methods=['GET', 'POST'])
@login_required
@role_forbidden(['default', 'vendor'])
def show_history():
    dates = get_filter_timestamps()
    filter_from = request.args.get('from', default=dates['recently'], type=int)
    dates['сегодня'] = dates.pop('daily')
    dates['неделя'] = dates.pop('weekly')
    dates['месяц'] = dates.pop('monthly')
    dates['квартал'] = dates.pop('quarterly')
    dates['год'] = dates.pop('annually')
    dates['недавно'] = dates.pop('recently')
    events = EventApi.get_entities(timestamp=filter_from)
    return render_template(
        'history.html',
        events=events,
        filter_from=filter_from,
        dates=dates
    )
