from flask_login import login_required
from flask import render_template

from app.main import bp
from app.utils import role_forbidden
from app.api.user import UserApi


################################################################################
# Responibility page
################################################################################


@bp.route('/help/', methods=['GET', 'POST'])
@login_required
@role_forbidden(['default', 'vendor'])
def show_help():
    project_responsibility = {}
    category_responsibility = {}
    users = UserApi.get_entities(role='validator') or []

    for user in users:
        for project in user['projects']:
            if project not in project_responsibility:
                project_responsibility[project] = {}
            position = user['position'] if user['position'] else 'не указана'
            if position not in project_responsibility[project]:
                project_responsibility[project][position] = []
            project_responsibility[project][position].append(user)

        for category in user['categories']:
            if category not in category_responsibility:
                category_responsibility[category] = {}
            position = user['position'] if user['position'] else 'не указана'
            if position not in category_responsibility[category]:
                category_responsibility[category][position] = []
            category_responsibility[category][position].append(user)

    return render_template(
        'help.html',
        projects=project_responsibility,
        categories=category_responsibility
    )
