from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from app.main import bp
from app.utils import role_required
from app.main.forms import CreateOrderForm
from app.main.utils import send_email_notification
from app.api.project import ProjectApi, OrderLimitApi, SiteApi
from app.api.hub import CategoryApi, ProductApi, VendorApi, AppSettingsApi
from app.api.order import OrderApi
from app.api.user import ResponsibilityApi
from app.utils import first


@bp.route('/shop/')
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def show_categories():
    return render_template(
        'shop_categories.html',
        projects=ProjectApi.get_entities() or [],
        limits=OrderLimitApi.get_entities() or [],
        categories=CategoryApi.get_entities() or []
    )


@bp.route('/shop/<int:cat_id>', defaults={'vendor_id': None})
@bp.route('/shop/<int:cat_id>/<int:vendor_id>')
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def shop_products(cat_id, vendor_id):

    category = first(CategoryApi.get_entities(id=cat_id))
    if category is None:
        return redirect(url_for('main.show_categories'))

    if vendor_id is not None:
        products = ProductApi.get_entities(cat_id=cat_id, vendor_id=vendor_id) or []
    else:
        products = ProductApi.get_entities(cat_id=cat_id) or []

    vendors = VendorApi.get_entities(cat_id=cat_id) or []

    return render_template(
        'shop_products.html',
        category=category,
        vendors=vendors,
        products=products,
        vendor_id=vendor_id
    )


@bp.route('/shop/cart', methods=['GET'])
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def shop_cart():
    form = CreateOrderForm()
    return render_template(
        'shop_cart.html',
        form=form
    )


@bp.route('/shop/order', methods=['POST'])
@login_required
@role_required(['initiative', 'purchaser', 'admin'])
def shop_order():
    form = CreateOrderForm()
    if form.validate_on_submit():

        project = first(ProjectApi.get_entities(id=form.project_id.data))
        if project is None:
            flash('???????????? ???? ????????????????????.')
            return redirect(url_for('main.shop_cart'))

        site = first(SiteApi.get_entities(id=form.site_id.data, project_id=project['id']))
        if site is None:
            flash('???????????? ???? ????????????????????.')
            return redirect(url_for('main.shop_cart'))

        ids = [p['product'] for p in form.cart.data]
        products = ProductApi.get_entities(ids=ids)
        products = {p['id']: p for p in products}
        cart = form.cart.data
        for item in cart:
            if item['product'] in products:
                item |= products[item['product']]
            else:
                del item

        if not cart:
            flash('???????????? ?????????????? ???? ?????????? ???????? ????????????.')
            return redirect(url_for('main.shop_cart'))

        categories = [p['category']['name'] for p in cart]
        responsibilities = ResponsibilityApi.get_entities(project=project['name'], categories=categories)

        app_settings = AppSettingsApi.get_entities()
        category = first(CategoryApi.get_entities(name=first(categories)))

        order = OrderApi.post_entity(
            project=project['name'],
            site=site['name'],
            products=cart,
            responsibilities=responsibilities,
            order_id_bias=app_settings.get('order_id_bias', 0),
            **(
                {
                    'income': category['income'],
                    'cashflow': category['cashflow'],
                    'budget_holder': category['budget_holder'],
                    'responsible': category['responsible']
                } if category else {}
            )
        )

        if order is None:
            flash('???? ?????????????? ?????????????? ????????????.')
        else:
            flash('???????????? ?????????????? ??????????????.')

    return redirect(url_for('main.shop_cart'))
