"""
Module registasi digunakan untuk registrasi pengguna secara online
URL: http://server/register
Rule registrasi
1. User melengkapi data registrasi termasuk photo kartu identitas
2. System memberikan response kepada user registrasi sudah ditermia dan status = -1 (tidak aktif)
3. User melakukan response dengan melakukan Click Link Response (Status menjadi 0)
4. Petugas melakukan verifikasi user
    a. Approve Apabila NIK(kode) sama dengan photo Kartu Identitas (Status=1)
    b. Tolak apabila NIK(kode) berbeda dengan photo Kartu Identitas (Status=-1)
5. System mengirim email hasil verifikasi
    a. Approve berisi email persetujuan yang berisi link sekali click
    b. Reject berisi email penolakan dyang didalamnya berisi juga link untuk edit data
        apabila user akan melakukan edit data.
        Link ini hanya bisa membuka data user yang status=-1

Parameter (Config)
1. base_register_approve: approve_file_template.tpl
2. base_register_reject: approve_file_template.tpl
File template tersebut dapat diunggah

Link dalam module registrasi:
1. Form registrasi http://server/register
2. List User yang melakukan registrasi yangu statusn=0 http://server/register/list
3. Form Verifikasi http://server/register/{uid}/verifikasi
4. Form edit registrasi http://server/register/{uid}/edit
5. Form Upload template
"""
import os
from email.utils import parseaddr

import colander
from deform import (widget, ValidationFailure, Button, FileData)
from opensipkd.tools import Upload
from opensipkd.tools.captcha import get_captcha
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from ziggurat_foundations.models.services.user import UserService

from opensipkd.base import get_params
from opensipkd.base.views.user import insert as save_user, email_validator
from opensipkd.base.views.user_login import send_email_security_code
from . import widget_os
from .base_views import store, image_validator, need_captcha, get_url_captcha
from ..models import User, DBSession, Partner, UserGroup
from ..views import BaseView

_ = TranslationStringFactory('user')


class AddSchema(colander.Schema):
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

    def after_bind(self, schema, kw):
        request = kw.get("request")
        is_id_card = get_params('reg_idcard')
        if is_id_card == '1' or is_id_card == "True" or is_id_card == "true":
            self["kode"] = colander.SchemaNode(
                colander.String(),
                widget=widget.TextInputWidget(),
                title="No.Identitas/NIK",
                # missing=colander.drop,
                oid="kode")
            self["doc_id_card"] = colander.SchemaNode(
                FileData(),
                widget=widget.FileUploadWidget(store),
                title="Photo Identitas",
                validator=image_validator)

        if not request.user and need_captcha():
            self["captcha"] = colander.SchemaNode(
                colander.String(),
                widget=widget_os.CaptchaWidget(url=get_url_captcha(request)),
                oid="captcha", title="Captcha")

        if request.user and request.user.id:
            self["password"] = colander.SchemaNode(
                colander.String(),
                widget=widget.PasswordWidget()
                , oid="password", title="Password")


class EditSchema(AddSchema):
    pass


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


def reg_buttons():
    btn_register = Button(name='save', css_class='btn-success', type="submit", title="Register")
    btn_cancel = Button(name='batal', css_class='btn-primary', type="submit")
    return btn_cancel, btn_register


class Registrasi(BaseView):
    def __init__(self, request):
        super(Registrasi, self).__init__(request)
        self.autocomplete = "off"
        self.buttons = reg_buttons()
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = User
        self.list_route = "home"

    def form_validator(self, form, value):
        form_exc = colander.Invalid(form, '')

        def err_captcha():
            msg = 'Captcha harus diisi'
            raise colander.Invalid(form['captcha'], msg)

        def err_email():
            exc = colander.Invalid(
                form['email'], 'e-mail %s sudah ada yang menggunakan' % value['email'])
            raise exc

        def err_user():
            raise colander.Invalid(
                form['user_name'], 'User name %s sudah ada yang menggunakan' % value['user_name'])

        def err_nik():
            if "kode" in form:
                raise colander.Invalid(
                    form['kode'], 'NIK %s sudah ada yang menggunakan' % value['kode'])
            else:
                raise colander.Invalid(
                    form['mobile'], 'Mobile %s sudah ada yang menggunakan' % value['kode'])

        def err_login():
            raise colander.Invalid(
                form["password"], 'User atau Password tidak sesuai')

        request = form.request
        is_logged = form.request.user
        email = value["email"]
        if "user_name" not in value or not value["user_name"]:
            value["user_name"] = value["mobile"]

        if 'user_name' in value:
            # Check Data User
            user_name = value["user_name"]
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
        if request.user:
            q = DBSession.query(Partner).filter_by(email=request.user.email)
            partner = q.first()
        else:
            partner = None

        found = email_found_partner(email)
        if partner:
            if found and found.id != partner.id:
                err_email()
        elif found:
            err_email()

        if "kode" not in value or not value["kode"]:
            value["kode"] = value["mobile"]

        if 'kode' in value:
            found_nik = nik_found(value['kode'])
            if partner:
                if found_nik and found_nik.id != partner.id:
                    err_nik()
            elif found_nik:
                err_nik()

        # Check Captcha jika registrasi
        if not request.user and need_captcha():
            if 'captcha' not in value or not value['captcha'] \
                    or 'captcha' not in request.session or not request.session['captcha']:
                err_captcha()

            captcha = 'captcha' in value and value['captcha'].upper() or None
            if not captcha or captcha != request.session['captcha']:
                del request.session["captcha"]
                err_captcha()

        if 'password' in value:
            user = form.request.user
            if not user or not UserService.check_password(user, value['password']):
                err_login()

    def before_save(self, row, values):
        if "doc_id_card" not in values or not values["doc_id_card"]:
            return row

        path = get_params('reg_folder', '/tmp/registrasi')
        if not os.path.exists(path):
            os.makedirs(path)

        upload = Upload(path)
        values["doc_id_card"] = upload.save(self.req, 'upload')
        row.doc_id_card = values["doc_id_card"]
        return row

    def before_edit(self, form):
        partner = DBSession.query(Partner). \
            join(User, Partner.email == User.email). \
            filter(User.id == self.req.user.id).first()
        if partner:
            values = {}
            for f in ["nama", "alamat_1", "alamat_2", "mobile", "email"]:
                values[f] = hasattr(partner, f) and getattr(partner, f) or ""
            form.set_appstruct(values)
        return form

    def after_save(self, row, values):
        if "old_email" in self.ses and self.ses["old_email"]:
            email = self.ses["old_email"]
            del self.ses["old_email"]
        else:
            email = row.email

        partner = Partner.query_email(email).first()
        if not partner:
            partner = Partner()
            partner.is_vendor = 0
            partner.is_customer = 1
            partner.status = 0

        partner.from_dict(values)
        DBSession.add(partner)
        DBSession.flush()
        return row

    @view_config(route_name='register', renderer='templates/form_input.pt')
    def view_add(self):
        request = self.req
        self.bindings = dict(user=None)
        if request.user:
            return HTTPFound(location=request.route_url("profile"))

        # self.captcha = need_captcha() and get_captcha(request) or ""
        return super(Registrasi, self).view_add()

    @view_config(route_name='profile', renderer='templates/form_input.pt',
                 permission='view')
    def es_reg_edt(self):
        request = self.req
        register_form = get_params("register_form")
        self.bindings = dict(user=self.req.user)
        if register_form:
            return HTTPFound(location=request.route_url(register_form))
        return super(Registrasi, self).view_edit()

    def query_id(self):
        return DBSession.query(User). \
            filter(User.id == self.req.user.id)

    def id_not_found(self):
        return
