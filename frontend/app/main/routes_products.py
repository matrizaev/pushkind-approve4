from base64 import b64encode
import io
from zipfile import ZipFile
from pathlib import Path

from flask import redirect, render_template, request, url_for, flash, current_app
from flask import send_file, session
from flask_login import current_user, login_required
import pandas as pd

from app.main import bp
from app.utils import role_forbidden, role_required
from app.main.forms import UploadProductsForm, UploadImagesForm
from app.main.forms import UploadProductImageForm
from app.main.forms import AddHubForm, AddVendorForm, EditHubForm, EditVendorForm
from app.api.hub import HubApi, ProductApi, CategoryApi, VendorApi
from app.api.user import UserApi
from app.producer import post_upload_images, get_upload_image_queue_size


################################################################################
# Vendor products page
################################################################################

@bp.route('/vendors/', methods=['GET'])
@bp.route('/vendors/show', methods=['GET'])
@login_required
@role_forbidden(['default', 'initiative'])
def show_vendors():

    forms = {}
    forms['add_hub'] = AddHubForm()
    forms['add_vendor'] = AddVendorForm()
    forms['edit_hub'] = EditHubForm()
    forms['edit_vendor'] = EditVendorForm()
    forms['products_form'] = UploadProductsForm()
    forms['images_form'] = UploadImagesForm()
    forms['product_image_form'] = UploadProductImageForm()

    vendor_id = request.args.get('vendor_id', type=int)
    hubs = HubApi.get_entities() or []
    categories = CategoryApi.get_entities() or []

    vendors = []
    products = []

    if current_user.hub_id is not None:
        vendors = VendorApi.get_entities() or []
        if current_user.role.name == 'vendor':
            if len(vendors) > 0:
                 vendor_id = vendors[0]['id']
            else:
                vendor_id = None
        else:
            for vendor in vendors:
                if vendor['id'] == vendor_id:
                    break
            else:
                if len(vendors) > 0:
                    vendor_id = vendors[0]['id']
                else:
                    vendor_id = None
        if vendor_id is not None:
            products = ProductApi.get_entities(vendor_id=vendor_id) or []

    queue_size = get_upload_image_queue_size()
    if queue_size > 0:
        flash(f'Очередь на загрузку изображений: {queue_size}')

    return render_template(
        'vendors.html',
        hubs=hubs,
        forms=forms,
        vendors=vendors,
        products=products,
        categories=categories,
        vendor_id=vendor_id,
        queue_size=queue_size
    )


@bp.route('/products/upload', methods=['POST'])
@login_required
@role_forbidden(['default', 'initiative', 'supervisor'])
def upload_products():

    if current_user.role.name == 'vendor':
        vendor = next(iter(VendorApi.get_entities() or []), None)
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = next(iter(VendorApi.get_entities(id=vendor_id) or []), None)

    if not vendor:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.show_vendors'))

    vendor_id = vendor['id']

    form = UploadProductsForm()
    if form.validate_on_submit():
        data = b64encode(form.products.data.read()).decode('utf-8')
        response = ProductApi.post_entity(
            products=data,
            vendor_id=vendor_id
        )
        if response is not None:
            flash('Список товаров успешно обновлён.')
        else:
            flash('Не удалось обновить список товаров.')
            return redirect(url_for('main.show_vendors', vendor_id=vendor_id))

        post_upload_images(vendor_id, data)

    else:
        for error in form.products.errors:
            flash(error)
    return redirect(url_for('main.show_vendors', vendor_id=vendor_id))


@bp.route('/products/upload/images', methods=['POST'])
@login_required
@role_forbidden(['default', 'initiative', 'supervisor'])
def upload_images():

    if current_user.role.name == 'vendor':
        vendor = next(iter(VendorApi.get_entities() or []), None)
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = next(iter(VendorApi.get_entities(id=vendor_id) or []), None)

    if not vendor:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.show_vendors'))

    vendor_id = vendor['id']

    form = UploadImagesForm()
    if form.validate_on_submit():
        products = ProductApi.get_entities(vendor_id=vendor_id) or []
        products = {p['sku']:p['id'] for p in products}
        with ZipFile(form.images.data, 'r') as zip_file:
            for zip_info in zip_file.infolist():
                if zip_info.is_dir() or zip_info.file_size > current_app.config['MAX_FILE_SIZE']:
                    continue
                file_name = Path(zip_info.filename)
                sku = file_name.stem
                if sku not in products:
                    continue
                zip_info.filename = sku
                static_path = Path(f'app/static/upload/vendor{vendor_id}')
                static_path.mkdir(parents=True, exist_ok=True)
                zip_file.extract(zip_info, static_path)
                static_path = static_path / zip_info.filename
                response = ProductApi.put_entity(
                    products[sku],
                    image=url_for('static', filename=Path(*static_path.parts[2:]))
                )
                if response is None:
                    flash(f'Не удалось загрузить изображение для {sku}.')
        flash('Файл с изображениями товаров успешно обработан.')
    else:
        for error in form.images.errors:
            flash(error)
    return redirect(url_for('main.show_vendors', vendor_id=vendor_id))


@bp.route('/products/download', methods=['GET'])
@login_required
@role_forbidden(['default', 'initiative', 'supervisor'])
def download_products():

    if current_user.role.name == 'vendor':
        vendor = next(iter(VendorApi.get_entities() or []), None)
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = next(iter(VendorApi.get_entities(id=vendor_id) or []), None)

    if not vendor:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.show_vendors'))

    vendor_id = vendor['id']

    products = ProductApi.get_entities(vendor_id=vendor_id) or []
    df = pd.DataFrame(products, columns=['name', 'sku', 'price', 'measurement', 'category', 'description', 'input_required', 'image'])
    df['image'] = df['image'].apply(lambda x: (request.base_url[:-18] + x) if x else None)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='products.xlsx'
    )


@bp.route('/products/<int:product_id>/upload/image', methods=['POST'])
@login_required
@role_forbidden(['default', 'initiative', 'supervisor'])
def upload_product_image(product_id):
    if current_user.role.name == 'vendor':
        vendor = next(iter(VendorApi.get_entities() or []), None)
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = next(iter(VendorApi.get_entities(id=vendor_id) or []), None)

    if not vendor:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.show_vendors'))

    vendor_id = vendor['id']

    product = next(iter(ProductApi.get_entities(id=product_id, vendor_id=vendor_id) or []), None)

    if not product:
        flash('Такой товар не найден.')
        return redirect(url_for('main.show_vendors'))

    vendor_id = vendor['id']

    form = UploadProductImageForm()
    if form.validate_on_submit():
        f = form.image.data
        file_name = Path(product['sku'])
        static_path = Path(f'app/static/upload/vendor{vendor_id}')
        static_path.mkdir(parents=True, exist_ok=True)
        full_path = static_path / file_name
        f.save(full_path)
        image = url_for('static', filename=(Path(*full_path.parts[2:])))
        response = ProductApi.put_entity(product_id, image=image)
        if response is not None:
            flash('Изображение товара успешно загружено.')
        else:
            flash('Не удалось загрузить изображение.')
    else:
        for error in form.image.errors:
            flash(error)
    return redirect(url_for('main.show_vendors', vendor_id=vendor_id))


@bp.route('/hub/add/', methods=['POST'])
@login_required
@role_required(['admin'])
def add_hub():
    form = AddHubForm()
    if form.validate_on_submit():
        hub_name = form.hub_name.data.strip()
        hub_email = form.email.data.strip().lower()
        response = HubApi.post_entity(name=hub_name, email=hub_email)
        if response is not None:
            flash('Хаб успешно создан.')
        else:
            flash('Не удалось создать хаб.')
    else:
        errors = (
            form.hub_name.errors +
            form.email.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_vendors'))


@bp.route('/vendor/add/', methods=['POST'])
@login_required
@role_required(['admin'])
def add_vendor():
    form = AddVendorForm()
    if form.validate_on_submit():
        vendor_name = form.vendor_name.data.strip()
        vendor_email = form.email.data.strip().lower()

        vendor_admin = UserApi.get_entities(email=vendor_email)
        if len(vendor_admin) > 0:
            flash('Адрес электронной почты занят.')
            return redirect(url_for('main.show_vendors'))

        response = VendorApi.post_entity(
            name=vendor_name,
            email=vendor_email,
            hub_id=form.hub_id.data
        )
        if response is not None:
            response = UserApi.post_entity(
                email=vendor_email,
                password=form.password.data,
                name=vendor_name,
                hub_id=form.hub_id.data,
                role='vendor'
            )
            if response is None:
                flash('Не удалось создать пользователя поставщика.')
            flash('Поставщик успешно создан.')
        else:
            flash('Не удалось создать поставщика.')
    else:
        errors = (
            form.hub_id.errors +
            form.vendor_name.errors +
            form.email.errors +
            form.password.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_vendors'))


@bp.route('/vendor/remove/<int:vendor_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_vendor(vendor_id):
    response = VendorApi.delete_entity(vendor_id)
    if response is not None:
        flash('Поставщик успешно удалён.')
    else:
        flash('Не удалось удалить этого поставщика.')
    return redirect(url_for('main.show_vendors'))


@bp.route('/hub/remove/<int:hub_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def remove_hub(hub_id):
    response = HubApi.delete_entity(hub_id)
    if response is not None:
        flash('Хаб успешно удалён.')
        if hub_id == current_user.hub_id:
            response = UserApi.put_entity(current_user.id, hub_id=None)
            token = UserApi.get_token(None, None, current_user.token)
            session['_user_id'] = token
    else:
        flash('Не удалось удалить этот хаб.')
    return redirect(url_for('main.show_vendors'))


@bp.route('/hub/edit/', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_hub():
    form = EditHubForm()
    if form.validate_on_submit():
        hub_id = form.hub_id.data
        data = {
            'name': form.hub_name.data.strip(),
            'enabled': form.enabled.data
        }
        response = HubApi.put_entity(hub_id, **data)
        if response is None:
            flash('Невозможно изменить хаб.')
        else:
            flash('Хаб успешно изменён.')
    else:
        errors = (
            form.hub_id.errors +
            form.hub_name.errors +
            form.enabled.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_vendors'))


@bp.route('/vendor/edit/', methods=['POST'])
@login_required
@role_required(['admin'])
def edit_vendor():
    form = EditVendorForm()
    if form.validate_on_submit():
        vendor_id = form.vendor_id.data
        data = {
            'name': form.vendor_name.data.strip(),
            'enabled': form.enabled.data
        }
        response = VendorApi.put_entity(vendor_id, **data)
        if response is None:
            flash('Не удалось изменить поставщика.')
        else:
            flash('Поставщик успешно изменён.')
    else:
        errors = (
            form.vendor_id.errors +
            form.vendor_name.errors +
            form.enabled.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.show_vendors'))


@bp.route('/settings/hub/', methods=['POST'])
@login_required
@role_required(['admin', 'supervisor'])
def switch_hub():
    hub_id = request.form.get('hub_id')
    hubs = HubApi.get_entities(id=hub_id)
    if len(hubs) == 0:
        flash('Этот хаб не зарегистрован в системе.')
    else:
        response = UserApi.put_entity(current_user.id, hub_id=hub_id)
        if response is None:
            flash('Невозможно изменить хаб.')
        else:
            flash('Хаб успешно изменён.')
            token = UserApi.get_token(None, None, current_user.token)
            session['_user_id'] = token
    return redirect(url_for('main.show_vendors'))
