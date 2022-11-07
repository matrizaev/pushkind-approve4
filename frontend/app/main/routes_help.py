from io import StringIO

from flask_login import current_user, login_required
from flask import render_template
import pandas as pd

from app.main import bp
from app.utils import role_forbidden
from app.api.user import UserApi
from app.api.hub import CategoryApi
from app.api.project import ProjectApi


################################################################################
# Responibility page
################################################################################


@bp.route('/help/', methods=['GET', 'POST'])
@login_required
@role_forbidden(['default', 'vendor'])
def show_help():

    # stats = pd.read_sql(
    #     f"""select '' as status, '' as `site_name`, '' as category_name, sum(total) as price, count(*) as `cnt` from `order`
    #     union all
    #     select o.status, s.name as site_name, c.name as category_name, sum(o.total) as price, count(*) as `cnt` from `order` o
    #     inner join site s on o.site_id = s.id
    #     inner join order_category oc on o.id = oc.order_id
    #     inner join category c on oc.category_id = c.id
    #     where o.hub_id = {current_user.hub_id}
    #     group by o.status, s.name, c.name
    #     order by o.status, s.name, c.name""",
    #     con=db.session.connection()
    #     )
    buf = StringIO()
    # stats['status'] = stats['status'].apply(lambda x: OrderStatus[x] if x != '' else '')
    # stats.rename(
    #     {
    #         'status': 'Статус',
    #         'site_name': 'Объект',
    #         'category_name': 'Категория',
    #         'price': 'Сумма',
    #         'cnt': 'Кол-во'
    #     },
    #     inplace=True,
    #     axis=1
    # )
    # stats.to_html(
    #     buf=buf,
    #     classes=["table", "table-striped", "table-sm"],
    #     float_format=lambda x: "{:.2f}".format(x),
    #     table_id="statsTable"
    # )
    # buf.seek(0)


    project_responsibility = {}
    category_responsibility = {}
    projects = ProjectApi.get_entities() or []
    categories = CategoryApi.get_entities() or []
    users = UserApi.get_entities(role='validator') or []

    for user in users:
        for project in projects:
            if project['name'] not in project_responsibility:
                project_responsibility[project['name']] = {}
            if project['id'] in user['projects']:
                position = user['position'] if user['position'] else 'не указана'
                if position not in project_responsibility[project['name']]:
                    project_responsibility[project['name']][position] = []
                project_responsibility[project['name']][position].append(user)

        for category in categories:
            if category['name'] not in category_responsibility:
                category_responsibility[category['name']] = {}
            if category['id'] in user['categories']:
                position = user['position'] if user['position'] else 'не указана'
                if position not in category_responsibility[category['name']]:
                    category_responsibility[category['name']][position] = []
                category_responsibility[category['name']][position].append(user)

    return render_template(
        'help.html',
        projects=project_responsibility,
        categories=category_responsibility,
        stats=buf
    )
