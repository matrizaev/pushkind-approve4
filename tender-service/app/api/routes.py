from io import BytesIO
from base64 import b64decode
from datetime import datetime

from flask import request, jsonify
import pandas as pd

from app import db
from app.api import bp
from app.models import Tender, TenderStatus, TenderVendor
from app.api.auth import token_auth
from app.api.errors import error_response


@bp.route('/tenders', methods=['GET'])
@token_auth.login_required(role=['admin', 'purchaser', 'vendor'])
def get_tenders():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    args = request.args.copy()
    vendor_id = args.pop('vendor_id', None)
    tenders = (
        Tender
        .query
        .filter_by(hub_id=current_user.hub_id)
        .filter_by(**args)
    )
    if current_user.role['name'] == 'vendor':
        tenders = tenders.join(TenderVendor).filter_by(vendor_id=current_user.email)
    tenders=tenders.all()
    return jsonify([t.to_dict(vendor_id) for t in tenders]), 200


@bp.route('/tender_statuses', methods=['GET'])
@token_auth.login_required
def get_tender_statuses():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    return jsonify([status.to_dict() for status in TenderStatus]), 200


@bp.route('/tender', methods=['POST'])
@token_auth.login_required(role=['admin', 'purchaser'])
def post_tender():
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    data = request.json or {}
    if data.get('products') is None:
        return error_response(400, 'Необходимые поля отсутствуют.')
    buf = BytesIO(b64decode(data['products'].encode()))
    buf.seek(0)
    df = pd.read_excel(
        buf,
        engine='openpyxl'
    )
    df.columns = df.columns.str.lower()
    if not all(col in df.columns for col in ('sku', 'name', 'quantity','measurement','description')):
        return error_response(400, 'Необходимые поля отсутствуют.')
    df = (
        df
        .drop(
            df.columns.difference([
                'sku',
                'name',
                'quantity',
                'measurement',
                'description'
            ]),
            axis=1
        )
        .astype(
            dtype = {
                'sku': str,
                'name': str,
                'quantity': int,
                'measurement': str,
                'description': str
            }
        )
        .dropna(subset=['sku', 'name', 'quantity', 'measurement'])
        .drop_duplicates(subset='sku')
        .sort_values('sku')
    )
    tender = Tender(
        hub_id=current_user.hub_id,
        initiative_id=current_user.id,
        initiative={
            'name': current_user.name,
            'role': current_user.role,
            'email': current_user.email,
            'position': current_user.position,
            'location': current_user.location,
            'phone': current_user.phone
        },
        timestamp=datetime.now(),
        products=df.to_dict(orient='records'),
        status=TenderStatus.new
    )
    db.session.add(tender)
    db.session.commit()
    return jsonify(tender.to_dict()), 201


@bp.route('/tender/<int:tender_id>', methods=['PUT'])
@token_auth.login_required(role=['admin', 'purchaser', 'vendor'])
def put_tender(tender_id):
    current_user = token_auth.current_user()
    if current_user.hub_id is None:
        return error_response(404, 'Хаб не существует.')
    tender = Tender.query.filter_by(id=tender_id, hub_id=current_user.hub_id).first()
    data = request.json or {}
    if tender is None:
        return error_response(404, 'Тендер не существует.')
    if data.get('vendors') is not None and current_user.role['name'] in ('admin', 'purchaser'):
        for vendor in data['vendors']:
            tender_vendor = TenderVendor.query.filter_by(tender_id=tender_id, vendor_id=vendor['email'].lower()).first()
            if tender_vendor is not None:
                continue
            tender_vendor = TenderVendor(
                tender_id=tender_id,
                vendor_id=vendor['email'].lower(),
                vendor=vendor
            )
            db.session.add(tender_vendor)
            db.session.commit()
    if data.get('products') is not None:
        if current_user.role['name'] in ('admin', 'purchaser'):
            vendor_id = data.get('vendor_id')
            if vendor_id is None:
                return error_response(400, 'Необходимые поля отсутствуют.')
        else:
            vendor_id = current_user.email
        tender_vendor = TenderVendor.query.filter_by(tender_id=tender_id, vendor_id=vendor_id.lower()).first()
        if tender_vendor is None:
            return error_response(404, 'Тендер не существует.')
        buf = BytesIO(b64decode(data['products'].encode()))
        buf.seek(0)
        df = pd.read_excel(
            buf,
            engine='openpyxl'
        )
        df.columns = df.columns.str.lower()
        if not all(col in df.columns for col in ('sku', 'name', 'price','measurement','description')):
            return error_response(400, 'Необходимые поля отсутствуют.')
        df = (
            df
            .drop(
                df.columns.difference([
                    'sku',
                    'name',
                    'price',
                    'measurement',
                    'description'
                ]),
                axis=1
            )
            .astype(
                dtype = {
                    'sku': str,
                    'name': str,
                    'price': float,
                    'measurement': str,
                    'description': str
                }
            )
            .dropna(subset=['sku', 'name', 'price', 'measurement'])
            .drop_duplicates(subset='sku')
        )
        products = pd.DataFrame(tender.products)
        products = (
            products
            .drop(
                products.columns.difference([
                    'sku'
                ]),
                axis=1
            )
            .merge(df, how='left', on='sku', sort=True, suffixes=[None, None])
        )
        tender_vendor.products = products.to_dict(orient='records')
        db.session.commit()
    return jsonify(tender.to_dict()), 200
