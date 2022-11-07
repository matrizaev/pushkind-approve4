from base64 import b64encode

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.main import bp
from app.main.forms import UploadProductsForm, LeaveCommentForm
from app.utils import role_required
from app.api.tender import TenderApi
from app.api.hub import VendorApi
from app.api.event import EventApi


################################################################################
# Tenders page
################################################################################

@bp.route('/tenders/')
@bp.route('/tenders/show')
@login_required
@role_required(['admin', 'purchaser', 'vendor'])
def show_tenders():
    form = UploadProductsForm()
    return render_template(
        'tenders.html',
        form=form,
        tenders=TenderApi.get_entities() or []
    )


@bp.route('/tender/add', methods=['POST'])
@login_required
@role_required(['admin', 'purchaser'])
def add_tender():
    form = UploadProductsForm()
    if form.validate_on_submit():
        data = b64encode(form.products.data.read()).decode('utf-8')
        response = TenderApi.post_entity(
            products=data
        )
        if response is not None:
            flash('Тендер успешно создан.')
        else:
            flash('Не удалось создать тендер.')
    else:
        for error in form.products.errors:
            flash(error)
    return redirect(url_for('main.show_tenders'))


@bp.route('/tender/<int:tender_id>')
@login_required
@role_required(['admin', 'purchaser', 'vendor'])
def show_tender(tender_id):
    if current_user.role.name == 'vendor':
        vendor_id = current_user.email
    else:
        vendor_id=request.args.get('vendor_id', False)
    tender = next(iter(TenderApi.get_entities(id=tender_id, vendor_id=vendor_id)) or []) or None
    if tender is None:
        flash('Тендер не найден')
        return redirect(url_for('main.show_tenders'))

    comment_form = LeaveCommentForm()
    propose_form = UploadProductsForm()
    if current_user.role.name in ('admin', 'purchase'):
        vendors = VendorApi.get_entities() or []
        comment_form.notify_reviewers.choices = [
            (v['email'].lower(), v['name']) for v in vendors
        ]
    else:
        comment_form.notify_reviewers.choices = [
            (tender['initiative']['email'].lower(), tender['initiative']['name'])
        ]
    return render_template(
        'select.html',
        tender=tender,
        vendor_id=vendor_id,
        events=EventApi.get_entities(entity_id=tender_id, entity_type='tender') or [],
        comment_form=comment_form,
        propose_form=propose_form
    )


@bp.route('/tender/invite/<int:tender_id>', methods=['POST'])
@login_required
@role_required(['admin', 'purchaser'])
def invite_tender(tender_id):
    tender = next(iter(TenderApi.get_entities(id=tender_id)) or []) or None
    if tender is None:
        flash('Тендер не найден')
        return redirect(url_for('main.show_tenders'))

    vendors = VendorApi.get_entities() or []

    form = LeaveCommentForm()
    form.notify_reviewers.choices = [
        (v['email'].lower(), v['name']) for v in vendors
    ]
    if form.validate_on_submit():
        vendors = filter(lambda v: v['email'].lower() in form.notify_reviewers.data, vendors)
        response = TenderApi.put_entity(
            tender_id,
            vendors=list(vendors)
        )
        if response:
            comment = form.comment.data.strip()
            response = EventApi.post_entity(
                entity_id=tender_id,
                entity_type='tender',
                event_type='invited',
                data=comment
            )
            flash('Поставщики приглашены в тендер.')
        else:
            flash('Не удалось пригласить поставщиков.')
    else:
        for error in form.comment.errors + form.notify_reviewers.errors:
            flash(error)
    return redirect(url_for('main.show_tender', tender_id=tender_id))


@bp.route('/tender/comment/<int:tender_id>', methods=['POST'])
@login_required
@role_required(['admin', 'purchaser', 'vendor'])
def comment_tender(tender_id):
    return redirect(url_for('main.show_tender', tender_id=tender_id))


@bp.route('/tender/cancel/<int:tender_id>', methods=['POST'])
@login_required
@role_required(['admin', 'purchaser'])
def cancel_tender(tender_id):
    return redirect(url_for('main.show_tender', tender_id=tender_id))


@bp.route('/tender/propose/<int:tender_id>', methods=['POST'])
@login_required
@role_required(['admin', 'purchaser', 'vendor'])
def propose_tender(tender_id):
    if current_user.role.name == 'vendor':
        vendor_id = current_user.email
    else:
        vendor_id=request.args.get('vendor_id', False)
    tender = next(iter(TenderApi.get_entities(id=tender_id, vendor_id=vendor_id)) or []) or None
    if tender is None:
        flash('Тендер не найден')
        return redirect(url_for('main.show_tenders'))

    form = UploadProductsForm()
    if form.validate_on_submit():
        data = b64encode(form.products.data.read()).decode('utf-8')
        response = TenderApi.put_entity(
            tender_id,
            products=data
        )
        if response is not None:
            flash('Предложение успешно загружено.')
        else:
            flash('Не удалось загрузить предложение.')
    else:
        for error in form.products.errors:
            flash(error)
    return redirect(url_for('main.show_tender', tender_id=tender_id))
