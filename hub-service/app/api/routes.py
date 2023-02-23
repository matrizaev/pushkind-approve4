from base64 import b64decode
from io import BytesIO

import pandas as pd
from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response
from app.models import AppSettings, Category, Product, Vendor
from app.producer import post_entity_changed
from flask import jsonify, request
from sqlalchemy import func


@bp.route('/hubs', methods=['GET'])
@token_auth.login_required
def get_hubs():
    current_user = token_auth.current_user()
    hubs = (
        Vendor
        .query
        .filter_by(hub_id=None)
        .filter_by(**request.args)
    )
    if current_user['role']['name'] not in ('admin', 'supervisor'):
        hubs = hubs.filter_by(id=current_user['hub_id'])
    hubs = hubs.order_by(Vendor.name).all()
    return jsonify([v.to_dict() for v in hubs]), 200


@bp.route('/vendors', methods=['GET'])
@token_auth.login_required
def get_vendors():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    cat_id = args.pop('cat_id', None)
    vendors = (
        Vendor
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
    )
    if current_user['role']['name'] == 'vendor':
        vendors = vendors.filter_by(email=current_user['email'])
    if cat_id is not None:
        vendors = vendors.join(Product).filter_by(cat_id=cat_id)
    vendors = vendors.order_by(Vendor.name).all()
    return jsonify([v.to_dict() for v in vendors]), 200


@bp.route('/categories', methods=['GET'])
@token_auth.login_required
def get_categories():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    args = request.args.copy()
    with_products = bool(args.pop('with_products', None))
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    categories = (
        Category
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .filter_by(**args)
        .all()
    )
    return jsonify([c.to_dict(with_products) for c in categories]), 200


@bp.route('/products', methods=['GET'])
@token_auth.login_required
def get_products():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    args = request.args.copy()
    ids = args.poplist('ids')
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    products = (
        Product
        .query
        .filter_by(**args)
        .join(Vendor)
        .filter_by(hub_id=current_user['hub_id'])
    )
    if current_user['role']['name'] == 'vendor':
        products = products.filter_by(email=current_user['email'])
    if ids:
        products = products.filter(Product.id.in_(ids))
    products = products.all()
    return jsonify([p.to_dict() for p in products]), 200


@bp.route('/app_settings', methods=['GET'])
@token_auth.login_required
def get_app_settings():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    app_settings = (
        AppSettings
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .first()
    )
    if app_settings is None:
        app_settings = AppSettings(hub_id=hub.id)
        db.session.add(app_settings)
        db.session.commit()
    return jsonify(app_settings.to_dict()), 200


@bp.route('/hub', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_hub():
    data = request.get_json() or {}
    if data.get('email') is None or data['name'] is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    email = str(data.pop('email')).lower()
    hub = Vendor.query.filter_by(email=email).first()
    if hub is not None:
        return error_response(409, 'Адрес электронной почты занят.')
    hub = Vendor(email=email)
    hub.from_dict(data)
    db.session.add(hub)
    db.session.commit()
    return jsonify(hub.to_dict()), 201


@bp.route('/vendor', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_vendor():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if not all([data.get(key) is not None for key in ('email', 'name')]):
        return error_response(400, 'Необходимые поля отсутствуют.')
    email = str(data['email']).lower()
    vendor = Vendor.query.filter_by(email=email).first()
    if vendor is not None:
        return error_response(409, 'Адрес электронной почты занят.')
    vendor = Vendor(hub_id=hub.id, email=email)
    vendor.from_dict(data)
    db.session.add(vendor)
    db.session.commit()
    return jsonify(vendor.to_dict()), 201


@bp.route('/category', methods=['POST'])
@token_auth.login_required(role=['admin'])
def post_category():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('name') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    category = Category.query.filter(func.lower(Category.name)==func.lower(data['name']), Category.hub_id==hub.id).first()
    if category is not None:
        return error_response(409, 'Категория с таким именем существует.')
    category = Category(hub_id=hub.id)
    category.from_dict(data)
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@bp.route('/product', methods=['POST'])
@token_auth.login_required(role=['admin', 'vendor', 'validator', 'purchaser'])
def post_product():
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    if data.get('vendor_id') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    vendor = Vendor.query.get_or_404(data['vendor_id'])
    if current_user['role']['name'] == 'vendor' and vendor.email != current_user['email']:
        return error_response(403)
    if data.get('products') is not None:
        buf = BytesIO(b64decode(data['products'].encode()))
        buf.seek(0)
        df = pd.read_excel(
            buf,
            engine='openpyxl'
        )
        df.columns = df.columns.str.lower()
        if not all(key in df.columns for key in ('name', 'sku', 'price', 'category', 'measurement', 'description')):
            return error_response(400, 'Необходимые поля отсутствуют.')
        df.drop(
            df.columns.difference([
                'name',
                'sku',
                'price',
                'measurement',
                'category',
                'description'
            ]),
            axis=1,
            inplace=True
        )
        df = df.astype(
            dtype = {
                'name': str,
                'sku': str,
                'price': float,
                'measurement': str,
                'description': str,
                'category': str
            }
        )
        df['vendor_id'] = vendor.id
        categories = Category.query.filter_by(hub_id=current_user['hub_id']).all()
        categories = {c.name.lower():c.id for c in categories}
        df['cat_id'] = df['category'].apply(lambda x: categories.get(x.lower()))
        df.drop(['category'], axis=1, inplace=True)
        df.dropna(subset=['cat_id', 'name', 'sku', 'price', 'measurement'], inplace=True)
        df['name'] = df['name'].str.slice(0,128)
        df['sku'] = df['sku'].str.slice(0,128)
        df['measurement'] = df['measurement'].str.slice(0,128)
        df['description'] = df['description'].str.slice(0,512)
        df['image'] = df["sku"].apply(lambda x: f'/static/upload/vendor{vendor.id}/{x}')

        Product.query.filter_by(vendor_id=vendor.id).delete()
        db.session.commit()
        df.to_sql(name = 'product', con = db.engine, if_exists = 'append', index = False)
        db.session.commit()
        return jsonify({'status': 'success'}), 201
    else:
        if not all(data.get(key) is not None for key in ('name', 'sku', 'price', 'category', 'measurement', 'description')):
            return error_response(400, 'Необходимые поля отсутствуют.')
        category = Category.query.filter_by(hub_id=current_user['hub_id'], name=data['category']).first()
        if category is None:
            return error_response(404, 'Категория не существует.')
        product = Product.query.filter_by(sku=data['sku'], vendor_id=vendor.id).first()
        if product is not None:
            return error_response(409, 'Товар с таким артикулом существует.')
        product = Product(
            name=data['name'],
            sku=data['sku'],
            vendor_id=vendor.id,
            cat_id=category.id,
            price=data['price'],
            image=f'/static/upload/vendor{vendor.id}/{data["sku"]}',
            measurement=data['measurement'],
            description=data['description']
        )
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201


@bp.route('/hub/<int:hub_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_hub(hub_id):
    hub = Vendor.query.filter_by(id=hub_id).filter(Vendor.hub_id == None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    db.session.delete(hub)
    db.session.commit()
    post_entity_changed(hub_id, 'hub', None, 'removed') 
    return jsonify({'status': 'success'}), 200


@bp.route('/vendor/<int:vendor_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_vendor(vendor_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    vendor = Vendor.query.filter_by(id=vendor_id).filter(Vendor.hub_id != None).first()
    if vendor is None:
        return error_response(404, 'Поставщик не существует.')
    db.session.delete(vendor)
    db.session.commit()
    return jsonify({'status': 'success'}), 200


@bp.route('/category/<int:category_id>', methods=['DELETE'])
@token_auth.login_required(role=['admin'])
def delete_category(category_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return error_response(404, 'Категория не существует.')
    db.session.delete(category)
    db.session.commit()
    post_entity_changed(hub.id, 'category', category.name, 'removed')
    return jsonify({'status': 'success'}), 200


@bp.route('/product/<int:product_id>', methods=['DELETE'])
@bp.route('/product/', methods=['DELETE'], defaults={'product_id': None})
@token_auth.login_required(role=['admin', 'vendor', 'validator', 'purchaser'])
def delete_product(product_id):
    current_user = token_auth.current_user()
    args = request.args.copy()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    products = Product.query
    if product_id:
        products = products.filter_by(id=product_id, **args)
    products = products.join(Vendor).filter_by(hub_id=current_user['hub_id']).all()
    if not products:
        return error_response(404, 'Товар не существует.')
    for product in products:
        db.session.delete(product)
    db.session.commit()
    return jsonify({'status': 'success'}), 200


@bp.route('/hub/<int:hub_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_hub(hub_id):
    data = request.get_json() or {}
    hub = Vendor.query.filter_by(id=hub_id, hub_id = None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    hub.from_dict(data)
    db.session.commit()
    return jsonify(hub.to_dict()), 200


@bp.route('/vendor/<int:vendor_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_vendor(vendor_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    vendor = Vendor.query.filter_by(id=vendor_id).filter(Vendor.hub_id != None).first()
    if vendor is None:
        return error_response(404, 'Поставщик не существует.')
    vendor.from_dict(data)
    db.session.commit()
    return jsonify(vendor.to_dict()), 200


@bp.route('/category/<int:category_id>', methods=['PUT'])
@token_auth.login_required(role=['admin'])
def put_category(category_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return error_response(404, 'Категория не существует.')
    category.from_dict(data)
    db.session.commit()
    return jsonify(category.to_dict()), 200


@bp.route('/product/<int:product_id>', methods=['PUT'])
@token_auth.login_required(role=['admin', 'vendor', 'validator', 'purchaser'])
def put_product(product_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    product = Product.query.filter_by(id=product_id)
    if current_user['role']['name'] == 'vendor':
        vendor = Vendor.query.filter_by(email=current_user['email']).first()
        if vendor is None:
            return error_response(404, 'Поставщик не существует.')
        product = product.filter_by(vendor_id=vendor.id)
    else:
        product = product.join(Vendor).filter_by(hub_id=current_user['hub_id'])
    product = product.first()
    if product is None:
        return error_response(404, 'Товар не существует.')
    product.from_dict(data)
    db.session.commit()
    return jsonify(product.to_dict()), 200


@bp.route('/app_settings/<int:entity_id>', methods=['PUT', 'POST'])
@token_auth.login_required(role=['admin'])
def put_app_settings(entity_id):
    current_user = token_auth.current_user()
    hub = Vendor.query.filter_by(id=current_user['hub_id'], hub_id=None).first()
    if hub is None:
        return error_response(404, 'Хаб не существует.')
    data = request.get_json() or {}
    app_settings = (
        AppSettings
        .query
        .filter_by(hub_id=current_user['hub_id'])
        .first()
    )
    if app_settings is None:
        app_settings = AppSettings(hub_id=current_user['hub_id'])
    app_settings.from_dict(data)
    db.session.add(app_settings)
    db.session.commit()
    return jsonify({'status': 'success'}), 200
