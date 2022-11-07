from functools import wraps

from flask import current_app
from flask import render_template, url_for, jsonify
from flask_login import current_user

from app.email import SendEmail


################################################################################
# Utilities
################################################################################

def send_email_notification(kind, order, recipients_id=[], data=None):
    pass
    # recipients = (
    #     r for r in order.reviewers if (
    #         getattr(r, f'email_{kind}', False) is True and
    #         (r.id in recipients_id or len(recipients_id) == 0)
    #     )
    # )
    # for recipient in recipients:
    #     current_app.logger.info(
    #         '"%s" email about order %s has been sent to %s',
    #         kind,
    #         order.number,
    #         recipient.email
    #     )
    #     token = recipient.get_jwt_token(expires_in=86400)
    #     next_page=url_for('main.ShowOrder', order_id=order.id)
    #     SendEmail(
    #         f'Уведомление по заявке #{order.number}',
    #         sender=(current_app.config['MAIL_SENDERNAME'], current_app.config['MAIL_USERNAME']),
    #         recipients=[recipient.email],
    #         text_body=render_template(f'email/{kind}.txt', next_page=next_page, token=token, order=order, data=data),
    #         html_body=render_template(f'email/{kind}.html', next_page=next_page, token=token, order=order, data=data)
    #     )


def SendEmail1C(recipients, order, data):
    pass
    # current_app.logger.info(
    #     '"export1C" email about order %s has been sent to %s',
    #     order.number,
    #     recipients
    # )

    # if order.site is not None:
    #     subject = f'{order.site.project.name}. {order.site.name} (pushkind_{order.number})'
    # else:
    #     subject = f'pushkind_{order.number}'

    # data = (
    #     f'pushkind_{order.number}.xlsx',
    #     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #     data
    # )

    # SendEmail(
    #     subject,
    #     sender=(current_app.config['MAIL_SENDERNAME'], current_app.config['MAIL_USERNAME']),
    #     recipients=recipients,
    #     text_body=render_template('email/export1C.txt', order=order),
    #     html_body=render_template('email/export1C.html', order=order),
    #     attachments=[data]
    # )


def GetNewOrderNumber():
    pass
    # settings = AppSettings.query.filter_by(hub_id=current_user.hub_id).first()
    # order_id_bias = settings.order_id_bias if settings is not None else 0
    # count = db.session.query(Order).count() + order_id_bias
    # return f'{count}'
