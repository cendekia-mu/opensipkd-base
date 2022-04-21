import os
import re
from email.utils import parseaddr

import colander
from deform import (Form, widget, ValidationFailure, Button, FileData)
from opensipkd.base import get_params

from opensipkd.tools import get_settings, get_ext, Upload
from opensipkd.tools.captcha import get_captcha
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from ziggurat_foundations.models.services.user import UserService

from opensipkd.base.views.user import insert as save_user
from opensipkd.base.views.user_login import send_email_security_code
from .user_group import save as save_groups
from ..models import User, DBSession, Partner, Group, UserGroup
from ..views import BaseView

_ = TranslationStringFactory('user')


def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')


class NamaSchema(colander.Schema):
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    alamat_1 = colander.SchemaNode(
        colander.String(),
        title="Alamat",
        oid="alamat_1")
    alamat_2 = colander.SchemaNode(
        colander.String(),
        title="",
        missing=colander.drop,
        oid="alamat_2")
    mobile = colander.SchemaNode(
        colander.String(),
        oid="no_hp")
    email = colander.SchemaNode(
        colander.String(),
        title="E-mail",
        validator=email_validator,
        oid="email")


class Store(dict):
    def preview_url(self, name):
        return ""


store = Store()
reg_exts = ['.png', '.jpg', '.pdf', '.jpeg']

username_re = re.compile('^[a-z0-9_]{6,16}$', re.IGNORECASE)


def user_name_validator(node, value):
    if not username_re.match(value):
        raise colander.Invalid(node,
                               'Value must be between 6 and 16 characters and can only contain uppercase and lowercase alphanumeric characters or an underscore')


def id_card_validator(node, value):
    ext = get_ext(value["filename"])
    if ext not in reg_exts:
        raise colander.Invalid(node, f'Extension harus salahsatu dari {reg_exts}')


class RegSchema(colander.Schema):
    user_name = colander.SchemaNode(
        colander.String(),
        validator=user_name_validator,
        # colander.Length(max=16, max_err='Maximum ${max} Digit',
        #                           min=6, min_err='Minimimum ${min} Digit'),
        oid="user_name")

    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=18, max_err='Maximum ${max} Digit',
                                  min=15, min_err='Minimimum ${min} Digit'),
        title="No.Identitas/NIK",
        oid="kode")

    detail = NamaSchema()

    doc_id_card = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(store),
        validator=id_card_validator)

    # captcha = colander.SchemaNode(
    #     colander.String(),
    #     oid="captcha")

    def after_bin(self, schema, kwargs):
        request = kwargs["request"]
        if get_params('reg_idcard') != '1':
            del self["doc_id_card"]
        if get_params('reg_captcha') != '1':
            del self["captcha"]


class RegEditSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(readonly=True),
        title="No.Identitas/NIK",
        oid="kode")
    detail = NamaSchema()
    password = colander.SchemaNode(
        colander.String(),
        widget=widget.PasswordWidget(size=20),
        title="Password",
        oid="password")
    id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=widget.HiddenWidget(readonly=True),
    )
    doc_id_card = colander.SchemaNode(
        FileData(),
        widget=widget.String())

    def after_bin(self, schema, kwargs):
        request = kwargs["request"]
        self.kode["widget"] = widget.TextInputWidget(readonly=True)
        if "kode" not in request.params:
            self.kode["widget"] = widget.TextInputWidget()

        if "email" in request.params:
            self.detail.email["widget"] = widget.TextInputWidget(readonly=True)
            self.detail.email["missing"] = colander.drop

        if request.get_params('reg_id_card') != '0':
            del self["doc_id_card"]


# def user_name(user_name):
#     return User.get_by_identity(email)


def user_found(identity):
    return User.get_by_identity(identity)


def mobile_found_partner(mobile):
    return Partner.query_mobile(mobile)


def email_found_partner(email):
    return Partner.query_email(email).first()


def nik_found(nik):
    return Partner.query_kode(nik).first()


def _show_error(request, msg):
    request.session.flash(msg, 'error')


def show_error(request, msg):
    _show_error(request, msg)
    return HTTPFound(location=request.route_url('home'))

    # Validasi saat Register
    # 1. Cek email pada Users jika ada dan Users.id beda reject
    # 2. Cek email pada Partner jika ada dan Partner.id beda reject
    # 3. Cek NIK (kode) pada Partner jika ada dan Partner.id beda reject


def form_validator(form, value):
    value.update(value['detail'])
    form_exc = colander.Invalid(form, '')

    def err_captcha():
        msg = 'Captcha harus diisi'
        raise colander.Invalid(form['captcha'], msg)

    def err_email():
        exc = colander.Invalid(
            form['detail']['email'], 'e-mail %s sudah ada yang menggunakan' % value['email'])
        raise exc

    def err_user():
        raise colander.Invalid(
            form['user_name'], 'User name %s sudah ada yang menggunakan' % value['user_name'])

    def err_nik():
        raise colander.Invalid(
            form['kode'], 'NIK %s sudah ada yang menggunakan' % value['kode'])

    def err_login():
        raise colander.Invalid(
            form, 'User atau Password tidak sesuai')

    request = form.request
    # Check user_name
    user_name = value["user_name"]

    detail = value['detail']
    email = detail['email']

    # Check Data User
    is_logged = form.request.user
    user = user_found(user_name)
    if user and not is_logged:
        err_user()

    if user and is_logged:
        if user.id != is_logged.id:
            err_user()

    user = user_found(email)
    if user and not is_logged:
        err_email()
    if user and is_logged:
        if user.id != is_logged.id:
            err_email()

    # Check Data Partner
    if 'id' in request.matchdict:
        uid = request.matchdict['id']
        q = DBSession.query(Partner).filter_by(id=uid)
        partner = q.first()
    else:
        partner = None

    found = email_found_partner(email)
    if partner:
        if found and found.id != partner.id:
            err_email()
    elif found:
        err_email()

    # CEK NIK apakah Sudah Ada di tabel Partner?
    found_nik = nik_found(value['kode'])
    if partner:
        if found_nik and found_nik.id != partner.id:
            err_nik()
    elif found_nik:
        err_nik()

    # Check Captcha jika registrasi
    if not request.user:
        if get_params("reg_captcha") == '1':
            if 'captcha' not in value or not value['captcha'] \
                    or 'captcha' not in request.session or not request.session['captcha']:
                err_captcha()

            captcha = 'captcha' in value and value['captcha'].upper() or None

            if not captcha or captcha != request.session['captcha']:
                err_captcha()

    # Cek Old Password
    if 'password' in value:
        user = form.request.user
        if not user or not UserService.check_password(user, value['password']):
            err_login()


def get_form(request, class_form, buttons=('batal', 'simpan'),
             validator=form_validator):
    schema = class_form(validator=validator)
    schema = schema.bind(request=request)
    schema.request = request
    return Form(schema, buttons=buttons)


def save_partner(values, row=None):
    if not row:
        row = Partner()
        row.is_vendor = 0
        row.is_customer = 1
        row.status = 0
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(values, request, row=None):
    values.update(values['detail'])
    # disini yang di cek id partner
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']

    # Check registrant apakah sudah punya user atau belum
    if request.user:
        # Jika sudah punya user masukan ke group esppt
        user = request.user
        user_group = UserGroup.get_by_user(user)

        if user.email != values['email']:
            user.email = values['email']
            DBSession.add(user)
            DBSession.flush()
        values['status'] = 1

    else:
        # Jika Tidak Tambahkan User dan Kirim Email
        user_ = dict(user_name=values['user_name'],
                     email=values['email'])
        user, remain = save_user(request, user_)
        # if not external identity send security code
        if 'external' not in request.session or not request.session['external']:
            send_email_security_code(
                request, user, remain, 'Welcome new user', 'email-new-user',
                'email-new-user.tpl')
            data = dict(email=user.email)
            ts = _(
                'user-added',
                default='${email} berhasil ditambahkan dan email untuk ubah ' \
                        'kata kunci sudah dikirim.',
                mapping=data)
            request.session.flash(ts)

    if row:
        if row.email == row.kode:
            values['kode'] = values['email']
    else:
        if 'kode' not in values and not values['kode']:
            values['kode'] = values['email']

    values['user_id'] = user.id
    row = save_partner(values, row)
    ##Untuk SIMKEL##
    # settings = get_settings()
    # if 'default_group' in settings:
    #     groups = settings['default_group'].split(',')
    #     for group in groups:
    #         group_data = Group.query_group_name(group).first()
            # if not group_data:
            #     raise custom_error(-1, "Group Not Found.")
            # data = dict(group_id=group_data.id,
            #             user_id=user.id)
            # save_groups(data, None)
    return row


def route_list(request):
    return HTTPFound(location=request.route_url('home'))


def reg_buttons():
    btn_register = Button(name='register', css_class='btn-success', type="submit")
    btn_cancel = Button(name='batal', css_class='btn-primary', type="submit")

    return btn_cancel, btn_register


class RegistrasiAdd(BaseView):
    @view_config(route_name='register', renderer='templates/register.pt')
    def view_add(self):
        request = self.req
        if request.user:
            # partner = Partner.query_user_id(request.user.id).first()
            # if partner:
            return HTTPFound(location=request.route_url("profile"))

        form = get_form(request, RegSchema, reg_buttons())
        captcha = get_params("reg_captcha") and get_captcha(request) or None
        if request.POST:
            if 'register' in request.POST:
                # input_file = request.POST['upload'].file
                # filename = request.POST['upload'].filename.lower()
                # ext = get_ext(filename).lower()
                # raise ext
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), captcha=captcha, scripts="")

                values = dict(controls)
                path = get_params('reg_folder', '/tmp/registrasi')
                if not os.path.exists(path):
                    os.makedirs(path)

                upload = Upload(path)
                values["doc_id_card"] = upload.save(request, 'upload')

                save_request(values, request)
                request.session.flash('Registrasi Sukses.')

                if 'captcha' in request.session:
                    del (request.session['captcha'])

            return route_list(request)

        values = {}
        if request.user:
            values['email'] = request.user.email

        form.set_appstruct(values)
        return dict(form=form.render(), captcha=get_captcha(request),
                    scripts="")

    @view_config(route_name='profile', renderer='templates/register.pt',
                 permission='view')
    def es_reg_edt(self):
        request = self.req
        ses = request.session
        query = query_id(request)
        row = query.first()
        form = get_form(request, RegEditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    values = e.cstruct
                    values['kode'] = row.kode
                    form.set_appstruct(values)
                    return dict(form=form)

                save_request(dict(controls), request, row)
                request.session.flash('Sukses Update Profile.')

            return route_list(request)
        if row:
            values = row.to_dict()
            values['detail'] = row.to_dict()
        else:
            values = dict(detail=dict(email=request.user.email))

        form.set_appstruct(values)
        return dict(form=form.render(), scripts="")


########
# Edit #
########
def query_id(request):
    return DBSession.query(Partner). \
        join(User, Partner.email == User.email). \
        filter(User.id == request.user.id)


def id_not_found(request):
    msg = 'Register ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
