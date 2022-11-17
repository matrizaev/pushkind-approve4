from io import BytesIO

from flask_login import current_user, login_required
from flask import render_template, redirect, url_for, flash, send_file, request
import pandas as pd

from app.main import bp
from app.main.forms import UserRolesForm, UserSettingsForm
from app.main.forms import AddCategoryForm, ProjectForm, SiteForm, ProjectForm
from app.main.forms import EditCategoryForm
from app.main.forms import AppSettingsForm, BudgetHolderForm
from app.main.forms import IncomeForm, CashflowForm
from app.utils import role_required, role_forbidden
from app.api.user import RoleApi, UserApi
from app.api.hub import CategoryApi, AppSettingsApi
from app.api.project import ProjectApi, IncomeApi, CashflowApi, BudgetHolderApi
from app.utils import first


################################################################################
# Settings page
################################################################################


@bp.route('/settings/show', methods=['GET'])
@login_required
@role_forbidden(['default', 'vendor'])
def show_settings():

    forms = {
        'add_category': AddCategoryForm(),
        'edit_category': EditCategoryForm(),
        'project': ProjectForm(),
        'site': SiteForm(),
        'income': IncomeForm(),
        'cashflow': CashflowForm(),
        'budget_holder': BudgetHolderForm()
    }

    app_data = AppSettingsApi.get_entities()
    if app_data is not None:
        forms['app'] = AppSettingsForm(
            enable=app_data['notify_1C'],
            email=app_data['email_1C'],
            order_id_bias=app_data['order_id_bias']
        )
    else:
        forms['app'] = AppSettingsForm()

    projects = ProjectApi.get_entities() or []
    categories = CategoryApi.get_entities() or []
    incomes = IncomeApi.get_entities() or []
    cashflows = CashflowApi.get_entities() or []
    responsibles = UserApi.get_entities(role='purchaser') or []
    budget_holders = BudgetHolderApi.get_entities() or []
    roles = RoleApi.get_entities() or []

    forms['edit_category'].income.choices = [(i['name'], i['name']) for i in incomes]
    forms['edit_category'].cashflow.choices = [(c['name'], c['name']) for c in cashflows]
    forms['edit_category'].budget_holder.choices = [(b['name'], b['name']) for b in budget_holders]
    forms['edit_category'].responsible.choices = [(u['id'], u['name']) for u in responsibles]
    forms['edit_category'].income.choices.append((0, 'БДР...'))
    forms['edit_category'].cashflow.choices.append((0, 'БДДС...'))
    forms['edit_category'].budget_holder.choices.append((0, 'ФДБ...'))
    forms['edit_category'].responsible.choices.append((0, 'Ответственный...'))


    projects = ProjectApi.get_entities(enabled=1) or []
    categories = CategoryApi.get_entities() or []


    if current_user.role.name == 'admin':
        forms['user'] = UserRolesForm()
        forms['user'].role.choices = [
            (r['name'], r['pretty']) for r in roles
        ]
    else:
        forms['user'] = UserSettingsForm()

    if current_user.role.name in ('admin', 'purchaser', 'validator'):
        forms['user'].about_user.categories.choices = [
            c['name'] for c in categories
        ]
        forms['user'].about_user.projects.choices = [
            p['name'] for p in projects
        ]
    else:
        forms['user'].about_user.categories.choices = []
        forms['user'].about_user.projects.choices = []

    user = first(UserApi.get_entities(id=current_user.id))

    if current_user.role.name == 'admin':
        users = UserApi.get_entities() or []
    else:
        users = []

    return render_template(
        'settings.html',
        forms=forms,
        user=user,
        users=users,
        projects=projects,
        categories=categories,
        incomes=incomes,
        cashflows=cashflows,
        budget_holders=budget_holders,
        responsibles=responsibles
    )


@bp.route('/user/edit', methods=['POST'])
@login_required
@role_forbidden(['default', 'vendor'])
def edit_user():

    projects = ProjectApi.get_entities(enabled=1) or []
    categories = CategoryApi.get_entities() or []
    roles = RoleApi.get_entities() or []

    if current_user.role.name == 'admin':
        user_form = UserRolesForm()
        user_form.role.choices = [
            (r['name'], r['pretty']) for r in roles
        ]
    else:
        user_form = UserSettingsForm()

    if current_user.role.name in ('admin', 'purchaser', 'validator'):
        user_form.about_user.categories.choices = [
            c['name'] for c in categories
        ]
        user_form.about_user.projects.choices = [
            p['name'] for p in projects
        ]
    else:
        user_form.about_user.categories.choices = []
        user_form.about_user.projects.choices = []

    if user_form.submit.data:
        if user_form.validate_on_submit():
            if current_user.role.name == 'admin':
                user = {
                    'hub_id': current_user.hub_id,
                    'role': user_form.role.data,
                    'note': user_form.note.data,
                    'birthday': user_form.birthday.data.isoformat() if user_form.birthday.data else None,
                }
                user_id = user_form.user_id.data
            else:
                user = {'role': current_user.role.name}
                user_id = current_user.id

            user['phone'] = user_form.about_user.phone.data
            user['location'] = user_form.about_user.location.data
            user['email_new'] = user_form.about_user.email_new.data
            user['email_modified'] = user_form.about_user.email_modified.data
            user['email_disapproved'] = user_form.about_user.email_disapproved.data
            user['email_approved'] = user_form.about_user.email_approved.data
            user['email_comment'] = user_form.about_user.email_comment.data
            user['name'] = user_form.about_user.full_name.data.strip()
            user['position'] = user_form.about_user.position.data.strip().lower()

            if user['role'] in ('purchaser', 'validator'):
                user['categories'] = user_form.about_user.categories.data
                user['projects'] = user_form.about_user.projects.data

            response = UserApi.put_entity(user_id, **user)

            if response is not None:
                flash('Данные успешно сохранены.')
            else:
                flash('Не удалось сохранить пользователя.')
        else:
            errors = (
                user_form.about_user.full_name.errors +
                user_form.about_user.phone.errors +
                user_form.about_user.categories.errors +
                user_form.about_user.projects.errors +
                user_form.about_user.position.errors +
                user_form.about_user.location.errors +
                user_form.about_user.email_new.errors +
                user_form.about_user.email_modified.errors +
                user_form.about_user.email_approved.errors +
                user_form.about_user.email_disapproved.errors
            )
            if isinstance(user_form, UserRolesForm):
                errors += (
                    user_form.user_id.errors +
                    user_form.role.errors +
                    user_form.note.errors +
                    user_form.birthday.errors
                )
            for error in errors:
                flash(error)
        return redirect(url_for('main.show_settings'))


@bp.route('/users/remove', methods=['POST'])
@login_required
@role_required
def remove_user():
    if current_user.role.name == 'admin':
        user_id = request.form.get('user_id', type=int)
    else:
        user_id = current_user.id
    response = UserApi.delete_entity(user_id)
    if response is None:
        flash('Не удалось удалить пользователя.')
    else:
        flash('Пользователь успешно удалён.')
    if user_id != current_user.id:
        return redirect(url_for('main.show_settings'))
    else:
        return redirect(url_for('auth.logout'))


@bp.route('/users/download')
@login_required
@role_required(['admin'])
def download_users():
    users = UserApi.get_entities()
    df = pd.DataFrame(users)
    df.drop(
        df.columns.difference([
            'name',
            'phone',
            'email',
            'role',
            'location',
            'position',
            'note',
            'last_seen',
            'registered',
            'birthday'
        ]),
        axis=1,
        inplace=True
    )
    df['role'] = df['role'].apply(lambda x: x['pretty'])
    df.rename(
        {
            'name': 'ФИО',
            'phone': 'Телефон',
            'email': 'Email',
            'role': 'Права',
            'location': 'Площадка',
            'position': 'Роль',
            'note': 'Заметка',
            'last_seen': 'Активность',
            'registered': 'Регистрация',
            'birthday': 'День рождения'
        },
        axis=1,
        inplace=True
    )
    df['Согласованных заявок пользователя'] = ''
    df['Сумма согласованных заявок пользователя'] = ''
    df['Согласовал заявок'] = ''
    df['Должен согласовать заявок'] = ''
    df['Номер для согласования'] = ''

    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='users.xlsx'
    )
