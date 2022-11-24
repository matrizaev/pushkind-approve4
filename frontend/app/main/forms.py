import json
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, SelectField, TextAreaField, FieldList
from wtforms import FormField, Form, PasswordField, BooleanField, SelectMultipleField, DecimalField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Length, ValidationError, Email, InputRequired, Optional
from wtforms.fields import DateField
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize

from app.main.utils import send_email_notification
from app.api.event import EventApi


class JSONField(StringField):
    def _value(self):
        return json.dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError as exc:
                raise ValueError('Не корректное поле данных.') from exc
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            try:
                json.dumps(self.data)
            except TypeError as exc:
                raise TypeError('Не корректное поле данных.') from exc


################################################################################
# Approve page
################################################################################


class InitiativeForm(FlaskForm):
    project = SelectField(
        'Проект',
        validators=[DataRequired(message='Название проекта - обязательное поле.')],
        coerce=str
    )
    site = SelectField(
        'Объект',
        validators=[DataRequired(message='Название объекта - обязательное поле.')],
        coerce=str
    )
    categories = SelectMultipleField(
        'Категории',
        validators=[DataRequired(message='Категории заявки - обязательное поле.')],
        coerce=str
    )
    submit = SubmitField('Сохранить')


class ApproverForm(FlaskForm):
    income_statement = SelectField(
        'Статья БДР',
        validators=[DataRequired(message='Статья БДР - обязательное поле.')],
        coerce=str
    )
    cashflow_statement = SelectField(
        'Статья БДДС',
        validators=[DataRequired(message='Статья БДДС - обязательное поле.')],
        coerce=str
    )
    submit = SubmitField('Сохранить')


class LeaveCommentForm(FlaskForm):
    comment = TextAreaField(
        'Комментарий',
        validators=[
            Length(max=256, message='Слишком длинный комментарий.')
        ]
    )
    notify_reviewers = SelectMultipleField('Уведомить ↓')
    submit = SubmitField('Сохранить')

    def comment_and_send_email(self, entity_id, event_type, entity_type, reviewers):
        pass
        # stripped = self.comment.data.strip() or None
        # reviewers = {r.id:r.name for r in order.reviewers}
        # response = EventApi.post_entity(
        #     entity_id=entity_id,
        #     event_type=event_type,
        #     entity_type=entity_type,
        #     timestamp=datetime.now(tz=timezone.utc),
        #     data=stripped
        # )
        # if len(self.notify_reviewers.data) > 0:
        #     send_email_notification(
        #         'comment',
        #         order,
        #         self.notify_reviewers.data,
        #         data=self.comment.data
        #     )
        #     message = 'Уведомление выслано: '
        #     message += ', '.join(reviewers[r] for r in self.notify_reviewers.data)
        #     event = OrderEvent(
        #         user_id=current_user.id,
        #         order_id=order.id,
        #         type=EventType.notification,
        #         data=message,
        #         timestamp=datetime.now(tz=timezone.utc)
        #     )
        #     db.session.add(event)


class OrderApprovalForm(FlaskForm):
    product_id = IntegerField('Идентификатор товара', render_kw={'hidden': ''})
    comment = TextAreaField(
        'Замечание',
        validators=[Length(max=512, message='Слишком длинное замечание.')]
    )
    submit = SubmitField('Сохранить')


class ChangeQuantityForm(FlaskForm):
    product_id = IntegerField(
        'Идентификатор товара',
        validators=[DataRequired(message='ID товара - обязательное поле.')],
        render_kw={'hidden': ''}
    )
    product_quantity = IntegerField(
        'Количество товара',
        validators=[InputRequired(message='Невозможное значение количества.')],
        render_kw={'type': 'number', 'step': 1, 'min': 0}
    )
    submit = SubmitField('Сохранить')

    def validate_product_quantity(self, product_quantity):
        if product_quantity.data < 0:
            raise ValidationError('Количество не может быть меньше нуля.')

class SplitOrderForm(FlaskForm):
    products = JSONField(
        'products',
        validators=[InputRequired(message='Список позиций не может быть пустым.')]
    )
    submit = SubmitField('Разделить')


################################################################################
# Stores page
################################################################################

class AddHubForm(FlaskForm):
    hub_name = StringField(
        'Хаб',
        validators=[
            DataRequired(message='Название хаба - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    email = EmailField(
        'Электронная почта',
        validators=[
            DataRequired(message='Электронная почта - обязательное поле.'),
            Email(),
            Length(max=128, message='Слишком длинный электронный адрес.')
        ]
    )
    submit = SubmitField('Создать')


class EditHubForm(FlaskForm):
    hub_id = IntegerField(
        'ID хаба',
        validators=[DataRequired(message='ID хаба - обязательное поле.')]
    )
    hub_name = StringField(
        'Название',
        validators=[
            DataRequired(message='Название хаба - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    enabled = BooleanField('Включить хаб')
    submit = SubmitField('Изменить')


class AddVendorForm(FlaskForm):
    hub_id = IntegerField(
        'ID хаба',
        validators=[DataRequired(message='ID хаба - обязательное поле.')]
    )
    vendor_name = StringField(
        'Поставщик',
        validators=[
            DataRequired(message='Название поставщика - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    email = EmailField(
        'Электронная почта',
        validators=[
            DataRequired(message='Электронная почта - обязательное поле.'),
            Email(),
            Length(max=128, message='Слишком длинный электронный адрес.')
        ]
    )
    password = PasswordField('Пароль',
        validators=[
            DataRequired(message='Пароль поставщика - обязательное поле.')
        ]
    )
    submit = SubmitField('Создать')


class EditVendorForm(FlaskForm):
    vendor_id = IntegerField(
        'ID поставщика',
        validators=[DataRequired(message='ID поставщика - обязательное поле.')]
    )
    vendor_name = StringField(
        'Поставщик',
        validators=[
            DataRequired(message='Название поставщика - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    enabled = BooleanField('Включить поставщика')
    submit = SubmitField('Изменить')


################################################################################
# Settings page
################################################################################

class UserSettings(Form):
    full_name = StringField(
        'Имя',
        validators=[
            DataRequired(message='Имя - обязательное поле.'),
            Length(max=128, message='Слишком длинное имя.')
        ]
    )
    phone = StringField(
        'Телефон',
        validators=[
            Length(max=128, message='Слишком длинный телефон.')
        ]
    )
    categories = SelectMultipleField('Мои категории ↓', coerce=str)
    projects = SelectMultipleField('Мои проекты ↓', coerce=str)
    position = StringField(
        'Роль',
        validators=[
            InputRequired(message='Роль - обязательное поле.'),
            Length(max=128, message='Слишком длинная роль.')
        ]
    )
    location = StringField(
        'Площадка',
        validators=[
            Length(max=512, message='Слишком длинное название.')
        ]
    )
    email_new = BooleanField('Новые заявки')
    email_modified = BooleanField('Заявка изменена')
    email_disapproved = BooleanField('Заявка отклонена')
    email_approved = BooleanField('Заявка согласована')
    email_comment = BooleanField('Комментарий к заявке')


class UserRolesForm(FlaskForm):
    user_id = IntegerField(
        'Идентификатор пользователя',
        render_kw={'hidden': ''}
    )
    role = SelectField(
        'Права доступа',
        validators=[InputRequired(message='Некорректные права доступа пользователя.')],
        coerce=str
    )
    about_user = FormField(UserSettings, [DataRequired()])
    note = TextAreaField('Заметка')
    birthday = DateField('День рождения', validators=[Optional()])
    submit = SubmitField('Сохранить')


class UserSettingsForm(FlaskForm):
    about_user = FormField(UserSettings, [DataRequired()])
    submit = SubmitField('Сохранить')


################################################################################
# Index page
################################################################################

class MergeOrdersForm(FlaskForm):
    orders = JSONField(
        'orders',
        validators=[InputRequired(message='Список заявок не может быть пустым.')]
    )
    submit = SubmitField('Объединить')


class SaveOrdersForm(FlaskForm):
    orders = JSONField(
        'orders',
        validators=[InputRequired(message='Список заявок не может быть пустым.')]
    )


################################################################################
# Admin page
################################################################################

class AppSettingsForm(FlaskForm):
    email = EmailField(
        'Электронная почта 1С',
        validators=[
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    enable = BooleanField('Включить рассылку 1С')
    order_id_bias = IntegerField('Константа номеров заявок')
    image = FileField(label = 'Логотип (png)', validators=[
        FileAllowed(['png'], 'Разрешены только изображения PNG!'),
        FileSize(16000000)
    ])
    submit = SubmitField('Сохранить')


class ProjectForm(FlaskForm):
    project_name = StringField(
        'Название',
        validators=[
            DataRequired(message='Название проекта - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    uid = StringField(
        'Код',
        validators=[
            Optional(),
            Length(max=128, message='Слишком длинный код.')
        ]
    )
    enabled = BooleanField('Включить проект')
    submit = SubmitField('Сохранить')


class SiteForm(FlaskForm):
    project_id = IntegerField(
        'ID проекта',
        [
            DataRequired(message='ID проекта - обязательное поле.')
        ]
    )
    site_name = StringField(
        'Название',
        validators=[
            DataRequired(message='Название объекта - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    uid = StringField(
        'Код',
        validators=[
            Optional(),
            Length(max=128, message='Слишком длинный код.')
        ]
    )
    submit = SubmitField('Сохранить')


class AddCategoryForm(FlaskForm):
    category_name = StringField(
        'Название',
        validators=[
            DataRequired(message='Название категории - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    submit = SubmitField('Сохранить')


class EditCategoryForm(FlaskForm):
    category_id = IntegerField(
        'ID категории',
        validators=[DataRequired(message='ID категории - обязательное поле.')]
    )
    responsible = SelectField(
        'Ответственный',
        validators=[
            DataRequired(message='Ответственный - обязательное поле.')
        ],
        coerce=str
    )
    budget_holder = SelectField(
        'ФДБ',
        validators=[
            DataRequired(message='ФДБ - обязательное поле.')
        ],
        coerce=str
    )
    income = SelectField(
        'БДР',
        validators=[DataRequired(message='БДР - обязательное поле.')],
        coerce=str
    )
    cashflow = SelectField(
        'БДДС',
        validators=[DataRequired(message='БДДС - обязательное поле.')],
        coerce=str
    )
    code = StringField(
        'Код',
        validators=[
            DataRequired(message='Код категории - обязательное поле.'),
            Length(max=128, message='Слишком длинный код.')
        ]
    )
    image = FileField(label = 'Изображение', validators=[
        FileAllowed(['jpg', 'png'], 'Разрешены только изображения JPG и PNG!'),
        FileSize(16000000)
    ])
    submit = SubmitField('Сохранить')


class IncomeForm(FlaskForm):
    income_name = StringField(
        'БДР',
        validators=[
            DataRequired(message='БДР - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    submit = SubmitField('Сохранить')


class BudgetHolderForm(FlaskForm):
    budget_holder_name = StringField(
        'ФДБ',
        validators=[
            DataRequired(message='ФДБ - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    submit = SubmitField('Сохранить')


class CashflowForm(FlaskForm):
    cashflow_name = StringField(
        'БДДС',
        validators=[
            DataRequired(message='БДДС - обязательное поле.'),
            Length(max=128, message='Слишком длинное название.')
        ]
    )
    submit = SubmitField('Сохранить')


################################################################################
# Limits page
################################################################################

class AddLimitForm(FlaskForm):
    interval = SelectField(
        'Интервал',
        validators=[InputRequired(message='Некорректный интервал лимита.')],
        coerce=str
    )
    value = DecimalField(
        'Лимит',
        validators=[DataRequired(message='Лимит - обязательное поле.')]
    )
    project = SelectField(
        'Проект',
        validators=[DataRequired(message='Проект - обязательное поле.')],
        coerce=str
    )
    cashflow = SelectField(
        'БДДС',
        validators=[DataRequired(message='БДДС - обязательное поле.')],
        coerce=str
    )
    submit = SubmitField('Создать')


################################################################################
# Shop page
################################################################################

class CartItemForm(Form):
    product = IntegerField(
        'Идентификатор товара',
        validators=[DataRequired(message='ID товара - обязательное поле.')],
        render_kw={'hidden': ''}
    )
    quantity = IntegerField(
        'Количество товара',
        validators=[InputRequired(message='Невозможное значение количества.')],
        render_kw={'type': 'number', 'step': 1, 'min': 0}
    )
    text = TextAreaField(
        'Текст баннера'
    )
    def validate_quantity(self, quantity):
        if quantity.data < 0:
            raise ValidationError('Количество не может быть меньше нуля.')


class CreateOrderForm(FlaskForm):
    project_id = IntegerField(
        'ID проекта',
        validators=[DataRequired(message='ID проекта - обязательное поле.')],
        render_kw={'hidden': ''}
    )
    site_id = IntegerField(
        'ID объекта',
        validators=[DataRequired(
        message='ID объекта - обязательное поле.')],
        render_kw={'hidden': ''}
    )
    cart = FieldList(FormField(CartItemForm))
    submit = SubmitField('Отправить заявку на согласование')


################################################################################
# Vendor page
################################################################################

class UploadProductsForm(FlaskForm):
    products = FileField(label = 'Продукты', validators=[
        FileRequired('Разрешены только XLSX.'),
        FileAllowed(['xlsx'], 'Разрешены только XLSX.')
    ])
    submit = SubmitField('Загрузить')


class UploadImagesForm(FlaskForm):
    images = FileField(label = 'Изображения', validators=[
        FileRequired('Разрешены только zip архивы.'),
        FileAllowed(['zip'], 'Разрешены только zip архивы.')
    ])
    submit = SubmitField('Загрузить')


class UploadProductImageForm(FlaskForm):
    image = FileField(label = 'Изображение', validators=[
        FileRequired('Разрешены только изображения JPG и PNG!'),
        FileAllowed(['jpg', 'png'], 'Разрешены только изображения JPG и PNG!'),
        FileSize(16000000)
    ])
    submit = SubmitField('Загрузить')
