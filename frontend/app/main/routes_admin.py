from pathlib import Path

from app.api.hub import AppSettingsApi, CategoryApi
from app.api.project import BudgetHolderApi, CashflowApi, IncomeApi, ProjectApi, SiteApi
from app.api.user import UserApi
from app.main import bp
from app.main.forms import (
    AddCategoryForm,
    AppSettingsForm,
    BudgetHolderForm,
    CashflowForm,
    EditCategoryForm,
    IncomeForm,
    ProjectForm,
    SiteForm,
)
from app.utils import first, role_required
from flask import flash, redirect, url_for
from flask_login import current_user, login_required


@bp.route('/app_settings/save', methods=['POST'])
@login_required
@role_required(['admin'])
def save_app_settings():
    form = AppSettingsForm()
    if form.validate_on_submit():
        response = AppSettingsApi.put_entity(
            current_user.hub_id,
            notify_1C=form.enable.data,
            email_1C=form.email.data,
            order_id_bias=form.order_id_bias.data,
            single_category_orders=form.single_category_orders.data
        )
        if response is not None:
            flash('Настройки успешно сохранены.')
        else:
            flash('Не удалось сохранить настройки.')
        if form.image.data:
            f = form.image.data
            file_name = Path(f.filename)
            file_name = Path(f'logo{current_user.hub_id}{file_name.suffix}')
            upload_path = Path('app/static/upload')
            full_path = upload_path / file_name
            f.save(full_path)
    else:
        errors = (
            form.email.errors +
            form.enable.errors +
            form.order_id_bias.errors +
            form.image.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/category/edit/', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_category():
    form = EditCategoryForm()
    incomes = IncomeApi.get_entities() or []
    cashflows = CashflowApi.get_entities() or []
    responsibles = UserApi.get_entities(role='purchaser') or []
    budget_holders = BudgetHolderApi.get_entities() or []
    form.income.choices = [(i['name'], i['name']) for i in incomes]
    form.cashflow.choices = [(c['name'], c['name']) for c in cashflows]
    form.budget_holder.choices = [(b['name'], b['name']) for b in budget_holders]
    form.responsible.choices = [(u['email'], u['name']) for u in responsibles]
    if form.validate_on_submit():
        if form.image.data:
            f = form.image.data
            file_name = Path(f.filename)
            file_name = Path(f'category-{form.category_id.data}{file_name.suffix}')
            static_path = Path('app/static/upload')
            static_path.mkdir(parents=True, exist_ok=True)
            static_path = static_path / file_name
            f.save(static_path)
            file_name = Path(*static_path.parts[2:])
        else:
            file_name = None

        response = CategoryApi.put_entity(
            entity_id=form.category_id.data,
            responsible = first(filter(lambda x: x['email'] == form.responsible.data, responsibles)),
            budget_holder = form.budget_holder.data,
            code = form.code.data.strip(),
            income = form.income.data,
            cashflow = form.cashflow.data,
            **({'image': url_for('static', filename=file_name)} if file_name else {})
        )
        if response is not None:
            flash("Категория успешно отредактирована.")
        else:
            flash("Не удалось отредактировать категорию.")
    else:
        errors = (
            form.category_id.errors +
            form.responsible.errors +
            form.budget_holder.errors +
            form.income.errors +
            form.cashflow.errors +
            form.image.errors +
            form.code.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/project/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        response = ProjectApi.post_entity(
            name=form.project_name.data.strip(),
            uid=form.uid.data.strip() if form.uid.data is not None else None,
            enabled=form.enabled.data
        )
        if response is not None:
            flash('Проект добавлен.')
        else:
            flash('Не удалось добавить проект.')
    else:
        for error in form.project_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/site/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_site():
    form = SiteForm()
    if form.validate_on_submit():
        response = SiteApi.post_entity(
            name=form.site_name.data.strip(),
            uid=form.uid.data.strip() if form.uid.data is not None else None,
            project_id=form.project_id.data
        )
        if response is not None:
            flash('Объект добавлен.')
        else:
            flash('Не удалось добавить объект.')
    else:
        for error in form.site_name.errors + form.uid.errors + form.project_id.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/project/remove/<int:project_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_project(project_id):
    response = ProjectApi.delete_entity(project_id)
    if response is not None:
        flash('Проект удален.')
    else:
        flash('Не удалось удалить проект.')
    return redirect(url_for('main.show_settings'))


@bp.route('/project/edit/<int:project_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_project(project_id):
    form = ProjectForm()
    if form.validate_on_submit():
        response = ProjectApi.put_entity(
            entity_id=project_id,
            name=form.project_name.data.strip(),
            uid=form.uid.data.strip() if form.uid.data is not None else None,
            enabled=form.enabled.data
        )
        if response is not None:
            flash('Проект изменён.')
        else:
            flash('Не удалось изменить проект.')
    else:
        for error in form.project_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/site/remove/<int:site_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_site(site_id):
    response = SiteApi.delete_entity(site_id)
    if response is not None:
        flash('Объект удален.')
    else:
        flash('Не удалось удалить объект.')
    return redirect(url_for('main.show_settings'))


@bp.route('/site/edit/<int:site_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_site(site_id):
    form = SiteForm()
    if form.validate_on_submit():
        response = SiteApi.put_entity(
            entity_id=site_id,
            name=form.site_name.data.strip(),
            uid=form.uid.data.strip() if form.uid.data is not None else None
        )
        if response is not None:
            flash('Объект изменён.')
        else:
            flash('Не удалось изменить объект.')
    else:
        for error in form.site_id.errors + form.site_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/income/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_income():
    form = IncomeForm()
    if form.validate_on_submit():
        response = IncomeApi.post_entity(
            name=form.income_name.data.strip()
        )
        if response is not None:
            flash('БДР добавлен.')
        else:
            flash('Не удалось добавить БДР')
    else:
        for error in form.income_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/budget_holder/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_budget_holder():
    form = BudgetHolderForm()
    if form.validate_on_submit():
        response = BudgetHolderApi.post_entity(
            name=form.budget_holder_name.data.strip()
        )
        if response is not None:
            flash('ФДБ добавлен.')
        else:
            flash('Не удалось добавить ФДБ')
    else:
        for error in form.budget_holder_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/cashflow/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add_cashflow():
    form = CashflowForm()
    if form.validate_on_submit():
        response = CashflowApi.post_entity(
            name=form.cashflow_name.data.strip()
        )
        if response is not None:
            flash('БДДС добавлен.')
        else:
            flash('Не удалось добавить БДДС.')
    else:
        for error in form.cashflow_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/income/remove/<int:income_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_income(income_id):
    response = IncomeApi.delete_entity(income_id)
    if response is not None:
        flash('БДР удален.')
    else:
        flash('Не удалось удалить БДР.')
    return redirect(url_for('main.show_settings'))


@bp.route('/budget_holder/remove/<int:budget_holder_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_budget_holder(budget_holder_id):
    response = BudgetHolderApi.delete_entity(budget_holder_id)
    if response is not None:
        flash('ФДБ удален.')
    else:
        flash('Не удалось удалить ФДБ.')
    return redirect(url_for('main.show_settings'))


@bp.route('/cashflow/remove/<int:cashflow_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_cashflow(cashflow_id):
    response = CashflowApi.delete_entity(cashflow_id)
    if response is not None:
        flash('БДДС удален.')
    else:
        flash('Не удалось удалить БДДС.')
    return redirect(url_for('main.show_settings'))


@bp.route('/income/edit/<int:income_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_income(income_id):
    form = IncomeForm()
    if form.validate_on_submit():
        response = IncomeApi.put_entity(
            entity_id=income_id,
            name=form.income_name.data.strip()
        )
        if response is not None:
            flash('БДР изменён.')
        else:
            flash('Не удалось изменить БДР.')
    else:
        for error in form.income_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/budget_holder/edit/<int:budget_holder_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_budget_holder(budget_holder_id):
    form = BudgetHolderForm()
    if form.validate_on_submit():
        response = BudgetHolderApi.put_entity(
            entity_id=budget_holder_id,
            name=form.budget_holder_name.data.strip()
        )
        if response is not None:
            flash('ФДБ изменён.')
        else:
            flash('Не удалось изменить ФДБ.')
    else:
        for error in form.budget_holder_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/cashflow/edit/<int:cashflow_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_cashflow(cashflow_id):
    form = CashflowForm()
    if form.validate_on_submit():
        response = CashflowApi.put_entity(
            entity_id=cashflow_id,
            name=form.cashflow_name.data.strip()
        )
        if response is not None:
            flash('БДДС изменён.')
        else:
            flash('Не удалось изменить БДДС.')
    else:
        for error in form.cashflow_id.errors + form.cashflow_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/category/add/', methods=['POST'])
@login_required
@role_required(['admin'])
def add_category():
    form = AddCategoryForm()
    if form.validate_on_submit():
        category_name = form.category_name.data.strip()
        response = CategoryApi.post_entity(name=category_name)
        if response is not None:
            flash('Категория добавлена.')
        else:
            flash('Не удалось добавить категорию.')
    else:
        for error in form.category_name.errors:
            flash(error)
    return redirect(url_for('main.show_settings'))


@bp.route('/category/remove/<int:category_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_category(category_id):
    response = CategoryApi.delete_entity(category_id)
    if response is not None:
        flash('Категория удалена.')
    else:
        flash('Не удалось удалить категорию')
    return redirect(url_for('main.show_settings'))
