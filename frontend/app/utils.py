from functools import wraps
from datetime import datetime, timedelta, timezone

from flask_login import current_user
from flask import render_template


def role_required(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role.name not in roles_list:
                return render_template('errors/403.html'), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def role_forbidden(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role.name in roles_list:
                return render_template('errors/403.html'), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def get_filter_timestamps():
    now = datetime.now(tz=timezone.utc)
    today = datetime(now.year, now.month, now.day)
    week = today - timedelta(days=today.weekday())
    month = datetime(now.year, now.month, 1)
    recently = today - timedelta(days=42)
    quarter = datetime(now.year, 3 * ((now.month - 1) // 3) + 1, 1)
    year = datetime(now.year, 1, 1)
    dates = {
        'daily': int(today.timestamp()),
        'weekly': int(week.timestamp()),
        'monthly': int(month.timestamp()),
        'recently': int(recently.timestamp()),
        'quarterly': int(quarter.timestamp()),
        'annually': int(year.timestamp()),
    }
    return dates
