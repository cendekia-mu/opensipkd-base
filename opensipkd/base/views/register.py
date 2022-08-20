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
2. List User yang melakukan registrasi yang statusn=0 http://server/register/list
3. Form Verifikasi http://server/register/{uid}/verifikasi
4. Form edit registrasi http://server/register/{uid}/edit
5. Form Upload template
"""
import os
from datetime import datetime

import colander
from deform import (widget, Button, FileData, ValidationFailure)
from pyramid.threadlocal import get_current_registry

from opensipkd.tools import Upload, mem_tmp_store, image_validator
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import TranslationStringFactory
from pyramid.security import forget
from pyramid.view import view_config
from ziggurat_foundations.models.services.user import UserService

from opensipkd.base import get_params, partner_idcard_folder
from opensipkd.base.views.user import email_validator, add_member_count

from opensipkd.tools.buttons import btn_cancel, btn_register, btn_save
from . import widget_os
from .base_views import need_captcha, need_verify, get_url_captcha
from .user_login import regenerate_security_code, get_login_headers, \
    send_email_security_code, send_email_pending
from opensipkd.models import User, DBSession, Partner, Group, UserGroup, \
    ExternalIdentity
from ..views import BaseView

_ = TranslationStringFactory('user')


class AddSchema(colander.Schema):
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama",
        title=_("Name"),
    )
    alamat_1 = colander.SchemaNode(
        colander.String(),
        title=_("Address"),
        oid="alamat_1")
    alamat_2 = colander.SchemaNode(
        colander.String(),
        title="",
        missing=colander.drop,
        oid="alamat_2")
    mobile = colander.SchemaNode(
        colander.String(),
        oid="no_hp",
        title=_("Mobile")
    )
    email = colander.SchemaNode(
        colander.String(),
        title=_("E-mail"),
        validator=email_validator,
        oid="email")

    def after_bind(self, schema, kw):
        request = kw.get("request")
        is_id_card = get_params('reg_idcard')
        user = request.user
        external_user = user and user.external_identities.count() > 0 or False
        if user:
            self["email"].widget = widget.TextInputWidget(readonly=True)
            self["email"].missing = colander.drop
            self["email"].validator = None

        if is_id_card == '1' or is_id_card == "True" or is_id_card == "true":
            self["kode"] = colander.SchemaNode(
                colander.String(),
                widget=widget.TextInputWidget(),
                title=_("ID Number"),
                # missing=colander.drop,
                oid="kode")
            self["idcard"] = colander.SchemaNode(
                FileData(),
                widget=widget.FileUploadWidget(mem_tmp_store),
                title=_("ID Card"),
                validator=image_validator)

        if not request.user and need_captcha():
            self["captcha"] = colander.SchemaNode(
                colander.String(),
                widget=widget_os.CaptchaWidget(),
                oid="captcha", title=_("Captcha"))
        if request.user and request.user.id and not external_user:
            # todo: external user tidak ada password
            # validasi harusnya menggunakan authentikasi ke provider lagi
            self["password"] = colander.SchemaNode(
                colander.String(),
                widget=widget.PasswordWidget(),
                oid="password", title=_("Password")
            )


class EditSchema(AddSchema):
    def after_bind(self, schema, kw):
        super().after_bind(schema, kw)
        del self["email"]


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


# def reg_buttons():
#     btn_register = Button(name='save', css_class='btn-success', type="submit",
#                           title="Register")
#     btn_cancel = Button(name='batal', css_class='btn-primary', type="submit")
#     return btn_cancel, btn_register


class Registrasi(BaseView):
    def __init__(self, request):
        super(Registrasi, self).__init__(request)
        self.autocomplete = "off"
        self.buttons = (btn_register, btn_cancel)
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Partner
        self.list_route = "home"

    def form_validator(self, form, value):
        """
        Default "value"
            user_name = mobile
            kode = mobile
        Validasi saat Register
        1. Cek email pada Users jika ada dan Users.id beda reject
        2. Cek email pada Partner jika ada dan Partner.id beda reject
        3. Cek kode pada Partner jika ada dan Partner.id beda reject
        4. Cek mobile pada Partner jika ada dan Users.id beda reject
        """
        form_exc = colander.Invalid(form, '')
        request = form.request
        session = request.session

        def raise_err(field, msg):
            form_exc[field] = msg
            raise form_exc

        def err_captcha():
            msg = 'Captcha berbeda'
            raise_err('captcha', msg)

        def err_email():
            msg = 'e-mail %s sudah ada yang menggunakan' % value['email']
            raise_err('email', msg)

        def err_user():
            if 'user_name' in form:
                msg = 'User name %s sudah ada yang menggunakan' % value[
                    'user_name']
                raise_err('user_name', msg)
            else:
                msg = 'Email %s sudah ada yang menggunakan' % value['email']
                raise_err('email', msg)

        def err_nik():
            if "kode" in form:
                msg = 'NIK %s sudah ada yang menggunakan' % value['kode']
                raise_err('kode', msg)

            else:
                msg = 'Mobile %s sudah ada yang menggunakan' % value['kode']
                raise_err('mobile', msg)

        def err_login():
            msg = 'User atau Password tidak sesuai'
            raise_err('password', msg)

        if not request.user and need_captcha():
            captcha = 'captcha' in value and value['captcha'].upper() or None
            ses_captcha = request.session.pop('captcha')
            if captcha != ses_captcha:
                err_captcha()

        user = request.user
        if not "email" in value and "id_info" in session:
            value["email"] = session["id_info"]["email"]

        if not user and (
                "user_name" not in value or not value["user_name"]):
            value["user_name"] = value["email"]

        if 'user_name' in value:
            user_name = value["user_name"]
            found = user_found(user_name)
            if found and not user:
                err_user()

            if found and user:
                if user.id != found.id:
                    err_user()

        # Check Data Partner
        if user:
            q = DBSession.query(Partner).filter_by(email=user.email)
            partner = q.first()
        else:
            partner = None

        if not user:
            email = value["email"]
            found = user_found(email)
            if found and not user:
                err_email()

            if found and user:
                if user.id != found.id:
                    err_email()

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

        if 'password' in value:
            if not user or not UserService.check_password(
                    user, value['password']):
                err_login()

    def before_add(self):
        result = {}
        if "id_info" in self.ses and self.ses['id_info']:
            result = self.ses["id_info"]
            result.update(dict(
                nama=" ".join([result["given_name"], result["family_name"]])))
        if need_captcha():
            result.update(dict(captcha=get_url_captcha(self.req)))
        return result

    # def after_save(self, row, values):

    def cancel_act(self):
        forget(self.req)
        self.ses.delete()

    @view_config(route_name='register', renderer='templates/form.pt')
    def view_register(self):
        if "g_state" in self.req.cookies:
            if "id_info" not in self.ses or not self.ses["id_info"]:
                return HTTPFound(location=self.req.route_url("login"))

        request = self.req
        reg_form = get_params("reg_form")
        if reg_form:
            return HTTPFound(location=self.req.route_url(reg_form))

        self.bindings = dict(user=None)
        if request.user:
            return HTTPFound(location=request.route_url("profile"))

        return super(Registrasi, self).view_add()

    def query_id(self):
        return DBSession.query(Partner). \
            filter(Partner.email == self.req.user.email)

    def id_not_found(self):
        return

    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        partner = DBSession.query(Partner). \
            filter(Partner.email == self.req.user.email).first()
        if partner:
            fields = ["nama", "alamat_1", "alamat_2", "mobile", "email", "kode",
                      "idcard"]
            for f in fields:
                d[f] = hasattr(partner, f) and getattr(partner, f) or ""
            if "idcard" in d:
                if d["idcard"]:
                    filename = d["idcard"]
                    preview_url = "/".join(
                        [self.home, partner_idcard_folder, filename])
                    d["idcard"] = {"uid": filename.split(".")[0],
                                   "filename": filename,
                                   "preview_url": preview_url
                                   }
                else:
                    d.pop("idcard")
            else:
                d.pop("idcard")
        return d

    def before_add(self):
        email = self.req.user and self.req.user.email or ""
        return {"email": email}

    @view_config(route_name='profile', renderer='templates/form.pt',
                 permission='view')
    def view_profile(self):
        self.buttons = (btn_save, btn_cancel)
        reg_form = get_params("reg_form")
        if reg_form:
            return HTTPFound(location=self.req.route_url(reg_form))
        self.bindings = dict(user=self.req.user)
        resp = super(Registrasi, self).view_edit()
        if not resp:
            resp = super(Registrasi, self).view_add()
        return resp

    def save_request(self, values, row=None):
        if not "email" in values or not values["email"]:
            values["email"] = self.req.user and self.req.user.email or ""

        if "idcard" in values and values["idcard"]:
            if self.req.POST['upload'] != b'':
                path = get_params('idcard_folder', '/tmp/idcard')
                upload = Upload(path)
                values["idcard"] = upload.save(self.req, 'upload')
            else:
                values.pop("idcard")
        if not row:
            values["is_vendor"] = 0
            values["is_customer"] = 1
        row = super().save_request(values, row)
        if not self.req.user:  # User Baru
            if 'groups' in values and values['groups']:
                gr = Group.query_group_name(values['groups']).first()
                ug = UserGroup()
                ug.user_id = row.id
                ug.group_id = gr.id
                DBSession.add(ug)
                add_member_count(gr.id)
                DBSession.flush()
            user = User()
            user.email = row.email
            user.user_name = row.email
            user.registered_date=datetime.now()
            DBSession.add(user)
            DBSession.flush()
            remain = regenerate_security_code(user)
            send_email_security_code(
                self.req, row, remain, 'Welcome new user', 'email-new-user',
                'email-new-user.tpl')
            ts = _(
                'user-added',
                default='${email} berhasil ditambahkan dan email untuk ubah ' \
                        'kata kunci sudah dikirim.',
                mapping={"email": row.email})
            self.ses.flash(ts)
        return row

    def next_add(self, form, **kwargs):
        table = kwargs.get("table")
        resources = kwargs.get("resources")
        if 'register' in self.req.POST:
            controls = self.req.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                return dict(form=form.render(e.cstruct),
                            table=table and table.render() or None,
                            scripts=self.form_scripts, css=resources["css"],
                            js=resources["js"])
            values = dict(c)
            row = self.save_request(values)
            self.after_add(row, values)
        return self.route_list()
