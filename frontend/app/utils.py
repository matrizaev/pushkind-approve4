from functools import wraps
from datetime import datetime, timedelta, timezone
from typing import Any
from collections.abc import Iterable

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
        'daily':     {
            'value': int(today.timestamp()),
            'pretty': 'сегодня'
        },
        'weekly':    {
            'value': int(week.timestamp()),
            'pretty': 'неделя'
        },
        'monthly':   {
            'value': int(month.timestamp()),
            'pretty': 'месяц'
        },
        'recently':  {
            'value': int(recently.timestamp()),
            'pretty': 'недавно'
        },
        'quarterly': {
            'value': int(quarter.timestamp()),
            'pretty': 'квартал'
        },
        'annually':  {
            'value': int(year.timestamp()),
            'pretty': 'год'
        }
    }
    return dates


def first(items: Iterable) -> Any:
    return next(iter(items or []), None)
