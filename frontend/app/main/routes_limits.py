from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request

from app.main import bp
from app.utils import role_forbidden
from app.main.forms import AddLimitForm
from app.api.project import ProjectApi, CashflowApi, OrderLimitApi, OrderLimitIntervalApi


@bp.route('/limits/', methods=['GET'])
@bp.route('/limits/show', methods=['GET'])
@login_required
@role_forbidden(['default', 'vendor'])
def show_limits():

    filter_from = request.args.get('from', default=None, type=str)

    intervals = OrderLimitIntervalApi.get_entities() or []

    for interval in intervals:
        if interval['name'] == filter_from:
            filter_limits = {'interval': filter_from}
            break
    else:
        filter_from = None
        filter_limits = {}


    projects = ProjectApi.get_entities(enabled=1) or []
    cashflows = CashflowApi.get_entities() or []
    limits = OrderLimitApi.get_entities(**filter_limits) or []
    form = AddLimitForm()
    form.project.choices = [(p['id'], p['name']) for p in projects]
    form.cashflow.choices = [(c['id'], c['name']) for c in cashflows]
    form.interval.choices = [(i['name'], i['pretty']) for i in intervals]
    form.process()

    return render_template(
        'limits.html',
        limits=limits,
        intervals=intervals,
        filter_from=filter_from,
        form=form
    )


@bp.route('/limits/add', methods=['POST'])
@login_required
@role_forbidden(['default', 'vendor', 'supervisor', 'initiative'])
def add_limit():
    projects = ProjectApi.get_entities(enabled=1) or []
    cashflows = CashflowApi.get_entities() or []
    intervals = OrderLimitIntervalApi.get_entities() or []

    form = AddLimitForm()
    form.project.choices = [(p['id'], p['name']) for p in projects]
    form.cashflow.choices = [(c['id'], c['name']) for c in cashflows]
    form.interval.choices = [(i['name'], i['pretty']) for i in intervals]

    if form.validate_on_submit():
        limit = OrderLimitApi.post_entity(
            value = float(form.value.data),
            interval = form.interval.data,
            cashflow_id = form.cashflow.data,
            project_id = form.project.data
        )
        if limit is not None:
            flash('Лимит успешно добавлен.')
        else:
            flash('Не удалось добавить лимит.')
    else:
        for error in (
            form.interval.errors +
            form.value.errors +
            form.project.errors +
            form.cashflow.errors
        ):
            flash(error)
    # OrderLimit.update_current(
    #     current_user.hub_id,
    #     form.project.data,
    #     form.cashflow.data
    # )
    return redirect(url_for('main.show_limits'))


@bp.route('/limits/remove/<int:limit_id>', methods=['POST'])
@login_required
@role_forbidden(['default', 'vendor', 'supervisor', 'initiative'])
def remove_limit(limit_id):
    limit = OrderLimitApi.delete_entity(limit_id)
    if limit is not None:
        flash('Лимит успешно удалён.')
    else:
        flash('Не удалось удалить лимит')
    return redirect(url_for('main.show_limits'))
