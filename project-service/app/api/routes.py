from flask import request, jsonify
from sqlalchemy import func

from app import db
from app.api import bp
from app.models import Project, Site, IncomeStatement, CashflowStatement
from app.models import OrderLimit, OrderLimitsIntervals, BudgetHolder
from app.api.auth import token_auth
from app.api.errors import error_response
from app.producer import post_entity_changed


@bp.route('/projects', methods=['GET'])
@token_auth.login_required
def get_projects():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    projects = (
        Project
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**request.args.to_dict())
        .order_by(Project.name)
        .all()
    )
    return jsonify([p.to_dict() for p in projects]), 200


@bp.route('/sites', methods=['GET'])
@token_auth.login_required
def get_sites():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    sites = (
        Site
        .query
        .filter_by(**request.args)
        .join(Project)
        .filter_by(hub_id=current_user['hub_id'])
        .order_by(Site.name)
        .all()
    )
    return jsonify([s.to_dict() for s in sites]), 200


@bp.route('/budget_holders', methods=['GET'])
@token_auth.login_required
def get_budget_holders():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    budget_holders = (
        BudgetHolder
        .query
        .filter_by(**request.args)
        .filter_by(hub_id=current_user['hub_id'])
        .order_by(BudgetHolder.name)
        .all()
    )
    return jsonify([s.to_dict() for s in budget_holders]), 200


@bp.route('/incomes', methods=['GET'])
@token_auth.login_required
def get_incomes():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    incomes = (
        IncomeStatement
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**request.args)
        .order_by(IncomeStatement.name)
        .all()
    )
    return jsonify([i.to_dict() for i in incomes]), 200


@bp.route('/cashflows', methods=['GET'])
@token_auth.login_required
def get_cashflows():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    casflows = (
        CashflowStatement
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**request.args)
        .order_by(CashflowStatement.name)
        .all()
    )
    return jsonify([v.to_dict() for v in casflows]), 200


@bp.route('/order_limits', methods=['GET'])
@token_auth.login_required
def get_order_limits():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    interval = args.pop('interval', None)
    try:
        interval = OrderLimitsIntervals[interval]
    except KeyError:
        interval = None
    order_limits = (
        OrderLimit
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
    )
    if interval is not None:
        order_limits = order_limits.filter_by(interval=interval)
    order_limits = order_limits.all()
    return jsonify([v.to_dict() for v in order_limits]), 200


@bp.route('/order_limit_intervals', methods=['GET'])
@token_auth.login_required
def get_order_limit_intervals():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([i.to_dict() for i in OrderLimitsIntervals]), 200


@bp.route('/project/<int:project_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_project(project_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    project = Project.query.filter_by(id=project_id, hub_id=current_user['hub_id']).first()
    if project is None:
        return error_response(404, 'Проект не существует.')
    db.session.delete(project)
    db.session.commit()
    post_entity_changed(current_user['hub_id'], 'project', project.name, 'removed')
    return jsonify({'status': 'success'}), 200


@bp.route('/site/<int:site_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_site(site_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    site = Site.query.filter_by(id=site_id).join(Project).filter(Project.hub_id==current_user['hub_id']).first()
    if site is None:
        return error_response(404, 'Объект не существует.')
    db.session.delete(site)
    db.session.commit()
    return jsonify({'status': 'success'}), 200


@bp.route('/income/<int:income_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_income(income_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    income = IncomeStatement.query.filter_by(id=income_id, hub_id=current_user['hub_id']).first()
    if income is None:
        return error_response(404, 'Объект не существует.')
    db.session.delete(income)
    db.session.commit()
    post_entity_changed(current_user['hub_id'], 'income', income.name, 'removed')
    return jsonify({'status': 'success'}), 200


@bp.route('/budget_holder/<int:budget_holder_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_budget_holder(budget_holder_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    budget_holder = BudgetHolder.query.filter_by(id=budget_holder_id, hub_id=current_user['hub_id']).first()
    if budget_holder is None:
        return error_response(404, 'ФДБ не существует.')
    db.session.delete(budget_holder)
    db.session.commit()
    post_entity_changed(current_user['hub_id'], 'budget_holder', budget_holder.name, 'removed')
    return jsonify({'status': 'success'}), 200


@bp.route('/cashflow/<int:cashflow_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_cashflow(cashflow_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    cashflow = CashflowStatement.query.filter_by(id=cashflow_id, hub_id=current_user['hub_id']).first()
    if cashflow is None:
        return error_response(404, 'Объект не существует.')
    db.session.delete(cashflow)
    db.session.commit()
    post_entity_changed(current_user['hub_id'], 'cashflow', cashflow.name, 'removed')
    return jsonify({'status': 'success'}), 200


@bp.route('/order_limit/<int:order_limit_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin', 'purchaser'])
def delete_order_limit(order_limit_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    order_limit = OrderLimit.query.filter_by(id=order_limit_id, hub_id=current_user['hub_id']).first()
    if order_limit is None:
        return error_response(404, 'Объект не существует.')
    db.session.delete(order_limit)
    db.session.commit()
    return jsonify({'status': 'success'}), 200


@bp.route('/project', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_project():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    project = Project.query.filter(func.lower(Project.name)==func.lower(data['name']), Project.hub_id==current_user['hub_id']).first()
    if project is not None:
        return error_response(409, 'Проект с таким именем существует.')
    project = Project(hub_id=current_user['hub_id'])
    project.from_dict(data)
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@bp.route('/site', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_site():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None or data.get('project_id') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    project = Project.query.filter_by(id=data['project_id'], hub_id=current_user['hub_id']).first()
    if project is None:
        return error_response(409, 'Проект не существует.')
    site = Site.query.filter(func.lower(Site.name)==func.lower(data['name']), Site.project_id==data['project_id']).first()
    if site is not None:
        return error_response(409, 'Объект с таким именем существует.')
    site = Site(project_id=data['project_id'])
    site.from_dict(data)
    db.session.add(site)
    db.session.commit()
    return jsonify(site.to_dict()), 201


@bp.route('/income', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_income():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    income = IncomeStatement.query.filter(func.lower(IncomeStatement.name)==func.lower(data['name']), IncomeStatement.hub_id==current_user['hub_id']).first()
    if income is not None:
        return error_response(409, 'БДР с таким именем существует.')
    income = IncomeStatement(hub_id=current_user['hub_id'])
    income.from_dict(data)
    db.session.add(income)
    db.session.commit()
    return jsonify(income.to_dict()), 201


@bp.route('/cashflow', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_cashflow():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    cashflow = CashflowStatement.query.filter(func.lower(CashflowStatement.name)==func.lower(data['name']), CashflowStatement.hub_id==current_user['hub_id']).first()
    if cashflow is not None:
        return error_response(409, 'БДДС с таким именем существует.')
    cashflow = CashflowStatement(hub_id=current_user['hub_id'])
    cashflow.from_dict(data)
    db.session.add(cashflow)
    db.session.commit()
    return jsonify(cashflow.to_dict()), 201


@bp.route('/budget_holder', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_budget_holder():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    budget_holder = BudgetHolder.query.filter(func.lower(BudgetHolder.name)==func.lower(data['name']), BudgetHolder.hub_id==current_user['hub_id']).first()
    if budget_holder is not None:
        return error_response(409, 'ФДБ с таким именем существует.')
    budget_holder = BudgetHolder(hub_id=current_user['hub_id'])
    budget_holder.from_dict(data)
    db.session.add(budget_holder)
    db.session.commit()
    return jsonify(budget_holder.to_dict()), 201


@bp.route('/order_limit', methods=['POST'])
@token_auth.login_required(role=['admin', 'purchaser'])
def post_order_limit():
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if not all(data.get(key) for key in ('cashflow_id', 'project_id', 'interval')):
        return error_response(400, 'Необходимые поля отсутствуют.')
    project = Project.query.filter_by(id=data['project_id'], hub_id=current_user['hub_id']).first()
    if project is None:
        return error_response(409, 'Проект не существует.')
    cashflow = CashflowStatement.query.filter_by(id=data['cashflow_id'], hub_id=current_user['hub_id']).first()
    if cashflow is None:
        return error_response(409, 'БДДС не существует.')
    order_limit = OrderLimit(
        hub_id=current_user['hub_id'],
        cashflow_id=data['cashflow_id'],
        project_id=data['project_id']
    )
    order_limit.from_dict(data)
    db.session.add(order_limit)
    db.session.commit()
    return jsonify(order_limit.to_dict()), 201


@bp.route('/project/<int:project_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_project(project_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    project = Project.query.filter_by(id=project_id, hub_id=current_user['hub_id']).first()
    if project is None:
        return error_response(409, 'Проект не существует.')
    project_name = project.name
    project.from_dict(data)
    db.session.commit()
    if project_name != data.get('name'):
        post_entity_changed(current_user['hub_id'], 'project', [project_name, data['name']], 'renamed')
    return jsonify(project.to_dict()), 200


@bp.route('/site/<int:site_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_site(site_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    site = Site.query.filter_by(id=site_id).join(Project).filter(Project.hub_id==current_user['hub_id']).first()
    if site is None:
        return error_response(409, 'Объект не существует.')
    site.from_dict(data)
    db.session.commit()
    return jsonify(site.to_dict()), 200


@bp.route('/income/<int:income_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_income(income_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    income = IncomeStatement.query.filter_by(id=income_id, hub_id=current_user['hub_id']).first()
    if income is None:
        return error_response(409, 'БДР не существует.')
    income_name = income.name
    income.from_dict(data)
    db.session.commit()
    if income_name != data.get('name'):
        post_entity_changed(current_user['hub_id'], 'income', [income_name, data['name']], 'renamed')
    return jsonify(income.to_dict()), 200


@bp.route('/budget_holder/<int:budget_holder_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_budget_holder(budget_holder_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    budget_holder = BudgetHolder.query.filter_by(id=budget_holder_id, hub_id=current_user['hub_id']).first()
    if budget_holder is None:
        return error_response(409, 'ФДБ не существует.')
    budget_holder_name = budget_holder.name
    budget_holder.from_dict(data)
    db.session.commit()
    if budget_holder_name != data.get('name'):
        post_entity_changed(current_user['hub_id'], 'budget_holder', [budget_holder_name, data['name']], 'renamed')
    return jsonify(budget_holder.to_dict()), 200


@bp.route('/cashflow/<int:cashflow_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_cashflow(cashflow_id):
    current_user = token_auth.current_user()
    if current_user['hub_id'] is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    cashflow = CashflowStatement.query.filter_by(id=cashflow_id, hub_id=current_user['hub_id']).first()
    if cashflow is None:
        return error_response(409, 'БДДС не существует.')
    cashflow_name = cashflow.name
    cashflow.from_dict(data)
    db.session.commit()
    if cashflow_name != data.get('name'):
        post_entity_changed(current_user['hub_id'], 'cashflow', [cashflow_name, data['name']], 'renamed')
    return jsonify(cashflow.to_dict()), 200
