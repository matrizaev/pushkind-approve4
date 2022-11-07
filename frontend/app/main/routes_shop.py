from datetime import datetime, timezone
from unicodedata import category

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.main import bp
from app.utils import role_required
from app.main.forms import CreateOrderForm
from app.main.utils import send_email_notification, GetNewOrderNumber
from app.api.project import ProjectApi, OrderLimitApi
from app.api.hub import CategoryApi, ProductApi, VendorApi


@bp.route('/shop/')
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def show_categories():
    return render_template(
        'shop_categories.html',
        projects=ProjectApi.get_entities(),
        limits=OrderLimitApi.get_entities(),
        categories=CategoryApi.get_entities()
    )

@bp.route('/shop/<int:cat_id>', defaults={'vendor_id': None})
@bp.route('/shop/<int:cat_id>/<int:vendor_id>')
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def shop_products(cat_id, vendor_id):

    category = next(iter(CategoryApi.get_entities(id=cat_id) or []), None)
    if category is None:
        return redirect(url_for('main.show_categories'))

    if vendor_id is not None:
        products = ProductApi.get_entities(cat_id=cat_id, vendor_id=vendor_id)
    else:
        products = ProductApi.get_entities(cat_id=cat_id)

    vendors = VendorApi.get_entities(cat_id=cat_id)

    return render_template(
        'shop_products.html',
        category=category,
        vendors=vendors,
        products=products,
        vendor_id=vendor_id
    )

@bp.route('/shop/cart', methods=['GET', 'POST'])
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def shop_cart():
    form = CreateOrderForm()
    # if form.submit.data:
    #     if form.validate_on_submit():
    #         products = Product.query.filter(
    #             Product.id.in_(
    #                 p['product'] for p in form.cart.data
    #             )
    #         ).all()
    #         if len(products) == 0:
    #             flash('Заявка не может быть пуста.')
    #             return render_template(
    #                 'shop_cart.html',
    #                 form=form
    #             )
    #         site = Site.query.filter_by(
    #             id=form.site_id.data,
    #             project_id=form.project_id.data
    #         ).first()
    #         if site is None:
    #             flash('Такой площадки не существует.')
    #             return redirect(url_for('main.shop_cart'))
    #         order_products = []
    #         order_vendors = []
    #         categories = []
    #         products = {p.id:p for p in products}
    #         for cart_item in form.cart.data:
    #             product = products[cart_item['product']]
    #             if product is None:
    #                 continue
    #             categories.append(product.cat_id)
    #             order_vendors.append(product.vendor)
    #             order_product = {
    #                 'id': product.id,
    #                 'sku': product.sku,
    #                 'price': product.price,
    #                 'name': product.name,
    #                 'imageUrl': product.image,
    #                 'categoryId': product.cat_id,
    #                 'vendor': product.vendor.name,
    #                 'category': product.category.name,
    #                 'quantity': cart_item['quantity'],
    #                 'selectedOptions': [
    #                     {
    #                         'value': product.measurement
    #                     }
    #                 ]
    #             }
    #             if cart_item['text'] is not None:
    #                 order_product['selectedOptions'].append(
    #                     {
    #                         'value': cart_item['text']
    #                     }
    #                 )
    #             order_products.append(order_product)
    #         order_number = GetNewOrderNumber()
    #         now = datetime.now(tz=timezone.utc)
    #         categories = Category.query.filter(
    #             Category.id.in_(
    #                 categories
    #             )
    #         ).all()
    #         cashflow_id, income_id = max((c.cashflow_id,c.income_id) for c in categories)
    #         order = Order(
    #             number = order_number,
    #             initiative_id = current_user.id,
    #             create_timestamp = int(now.timestamp()),
    #             site_id = site.id,
    #             hub_id = current_user.hub_id,
    #             products = order_products,
    #             vendors=list(set(order_vendors)),
    #             total = sum([p['quantity']*p['price'] for p in order_products]),
    #             status = OrderStatus.new,
    #             cashflow_id = cashflow_id,
    #             income_id = income_id
    #         )
    #         db.session.add(order)
    #         order.categories = categories
    #         db.session.commit()
    #         order.update_positions()
    #         flash('Заявка успешно создана.')
    #         send_email_notification('new', order)
    #         return redirect(url_for('main.show_index'))
    #     else:
    #         flash('Что-то пошло не так.')
    return render_template(
        'shop_cart.html',
        form=form
    )
