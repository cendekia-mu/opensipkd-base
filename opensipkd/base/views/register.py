# """
# Module registasi digunakan untuk registrasi pengguna secara online
# URL: http://server/register
# Rule registrasi
# 1. User melengkapi data registrasi termasuk photo kartu identitas
# 2. System memberikan response kepada user registrasi sudah ditermia dan status = -1 (tidak aktif)
# 3. User melakukan response dengan melakukan Click Link Response (Status menjadi 0)
# 4. Petugas melakukan verifikasi user
#     a. Approve Apabila NIK(kode) sama dengan photo Kartu Identitas (Status=1)
#     b. Tolak apabila NIK(kode) berbeda dengan photo Kartu Identitas (Status=-1)
# 5. System mengirim email hasil verifikasi
#     a. Approve berisi email persetujuan yang berisi link sekali click
#     b. Reject berisi email penolakan dyang didalamnya berisi juga link untuk edit data
#         apabila user akan melakukan edit data.
#         Link ini hanya bisa membuka data user yang status=-1

# Parameter (Config)
# 1. base_register_approve: approve_file_template.tpl
# 2. base_register_reject: approve_file_template.tpl
# File template tersebut dapat diunggah

# Link dalam module registrasi:
# 1. Form registrasi http://server/register
# 2. List User yang melakukan registrasi yang statusn=0 http://server/register/list
# 3. Form Verifikasi http://server/register/{uid}/verifikasi
# 4. Form edit registrasi http://server/register/{uid}/edit
# 5. Form Upload template
# """
from calendar import c
import logging
from datetime import datetime
import re

import colander
from deform import (widget, FileData, ValidationFailure, Button)
from opensipkd.base import BASE_CLASS
from opensipkd.tools import Upload, mem_tmp_store, image_validator, date_from_str
from opensipkd.tools.buttons import btn_cancel, btn_save
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.i18n import TranslationStringFactory
# from pyramid.security import forget
# from pyramid.view import view_config
from ziggurat_foundations.models.services.user import UserService

# from opensipkd.base import get_params, get_id_card_folder
from opensipkd.base.views.user import email_validator, add_member_count
from ..models import User, DBSession, Partner, Group, UserGroup
from ..widgets import widget_os
# from .base_views import need_captcha, get_url_captcha
from .user_login import regenerate_security_code, send_email_security_code
from ..views import BaseView
# from .. import get_urls

_ = TranslationStringFactory('user')

_logging = logging.getLogger(__name__)


class AddSchema(colander.Schema):
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama",
        title=_("Name"),
    )
    alamat_1 = colander.SchemaNode(
        colander.String(),
        title=_("Address"),
        validator=colander.Length(max=128),
        oid="alamat_1")
    alamat_2 = colander.SchemaNode(
        colander.String(),
        title="",
        validator=colander.Length(max=128),
        missing=colander.drop,
        oid="alamat_2")
    kelurahan = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="kelurahan")
    kecamatan = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="kecamatan")
    kota = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="kota")
    provinsi = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="provinsi")
    mobile = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=18, min=8),
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
        is_id_card = BASE_CLASS.reg_id_card
        _logging.debug(f"after_bind: is_id_card={is_id_card}")
        user = request.user
        external_user = user and user.external_identities.count() > 0 or False
        if user:
            self["email"].widget = widget.TextInputWidget(readonly=True)
            self["email"].missing = colander.drop
            self["email"].validator = None

        if is_id_card:
            self["kode"] = colander.SchemaNode(
                colander.String(),
                widget=widget.TextInputWidget(),
                title=_("ID Number"),
                oid="kode")
            
            self["idcard"] = colander.SchemaNode(
                FileData(),
                widget=widget.FileUploadWidget(mem_tmp_store),
                title=_("ID Card"),
                missing=colander.drop,
                    validator=image_validator)
            # if request.is_xhr:
            #      if request.POST:
            #         self["idcard"] = colander.SchemaNode(
            #         FileData(),
            #         title=_("ID Card"),
            #         validator=image_validator)
            #      else:
            #         self["idcard"] = colander.SchemaNode(
            #             colander.String(),
            #             title=_("ID Card"),
            #             missing=colander.drop)


            # else:

               
        if BASE_CLASS.reg_nip:
            self["nip"] = colander.SchemaNode(
                colander.String(),
                title=_("NIP"),
                validator=colander.Length(max=18, min=18),
                missing=colander.drop,
                oid="nip")


        if not request.user and BASE_CLASS.reg_captcha:
            self["captcha"] = colander.SchemaNode(
                colander.String(),
                widget=widget_os.CaptchaWidget(
                    request=request,
                    url=request.static_url(BASE_CLASS.captcha_files)),
                oid="captcha", title=_("Captcha"))
            if request.is_xhr:
                self["captcha_text"] = colander.SchemaNode(
                    colander.String(),
                    widget = widget.TextInputWidget(),
                    missing=colander.drop,
                    )

        if request.user and request.user.id:
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


# def mobile_found_partner(mobile):
#     return Partner.query_mobile(mobile)


def email_found_partner(email):
    return Partner.query_email(email).first()


def nik_found(nik):
    return Partner.query_kode(nik).first()


# def _show_error(request, msg):
#     request.session.flash(msg, 'error')


# def show_error(request, msg):
#     _show_error(request, msg)
#     return HTTPFound(location=get_urls(request.route_url('home')))


# # def reg_buttons():

# #     btn_cancel = Button(name='batal', css_class='btn-primary', type="submit")
# #     return btn_cancel, btn_register


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.autocomplete = "off"
        btn_register = Button(name='save', css_class='btn-success', type="submit",
                          title="Register")
        self.buttons = (btn_register, btn_cancel)
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Partner
        self.list_route = "base-home"

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
        _logging.debug(value)
        form_exc = colander.Invalid(form, '')
        request = form.request
        session = request.session

        def raise_err(field, msg):
            form_exc[field] = msg
            raise form_exc

        # def err_captcha():
        #     msg = 'Captcha berbeda'
        #     raise_err('captcha', msg)

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

        # if not request.user and need_captcha():
        #     captcha = 'captcha' in value and value['captcha'].upper() or None
        #     ses_captcha = request.session.pop('captcha')
        #     if captcha != ses_captcha:
        #         err_captcha()

        user = request.user
        if "email" not in value and "id_info" in session:
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
            external_user = user and user.external_identities.count() > 0 or False
            if external_user:
                ext_user = UserService.by_user_name_and_security_code(
                    user.user_name, value['password'])
                if not ext_user:
                    err_login()
                user.security_code = None
                DBSession.add(user)
                DBSession.flush()
            else:
                if not user or not UserService.check_password(
                        user, value['password']):
                    err_login()

        # if self.req.is_xhr:
        #     if "upload" in value and value["upload"]:
        #         value["idcard"] = value["upload"]


        if "idcard" in value and value["idcard"]:
            idcard = value["idcard"]
            if "fp" in idcard and idcard["fp"] and idcard["fp"] != b'':
                path = BASE_CLASS.partner_doc
                _logging.debug(idcard["fp"])
                upload = Upload(path)
                value["idcard"] = upload.save_fp(idcard)
            else:
                value.pop("idcard")
        if not self.req.user:
            value["groups"] = "Guest"

        super().form_validator(form, value)

    def send_profile_password(self):
        user = self.req.user
        
        if not self.req.POST and user and user.external_identities.count() > 0:
            from datetime import timedelta
            remain = regenerate_security_code(user)
            five_minutes = timedelta(1.0 / 24 / 60)


            if remain>299:
                send_email_security_code(
                    self.req, user, remain, 'Request profile change', 'email-profile-password',
                    'email-profile-password.tpl')
            self.req.session.flash(
                "Security code/password update profile sudah dikirimkan ke %s \n Jika tidak ditemukan cari dalam SPAM" % user.email)
        
    def before_add(self):
        result = {}
        # email = self.req.user and self.req.user.email or ""
        # return {"email": email}

        if "id_info" in self.ses and self.ses['id_info']:
            result = self.ses["id_info"]
            result.update(dict(
                nama=" ".join([result["given_name"], result["family_name"]])))
            self.send_profile_password()

        # if BASE_CLASS.reg_captcha:
            # result.update(dict(captcha=self.req.static_url(BASE_CLASS.captcha_files)))

        if self.req.is_xhr:
            url = self.req.static_url(BASE_CLASS.captcha_files)
            kode_captcha, file_name = widget_os.img_captcha(self.req)
            self.ses["captcha"] = kode_captcha
            result.update(dict(captcha=url+file_name,
                               captcha_text=kode_captcha))
        return result

#     # def after_save(self, row, values):

#     def cancel_act(self):
#         forget(self.req)
#         self.ses.delete()

    def view_register(self):
        request = self.req
        if not BASE_CLASS.allow_register:
            return HTTPFound(location=request.route_url("base-home"))
        if request.user:
            return HTTPFound(location=request.route_url("base-profile"))

        self.bindings = dict(user=None)
        if "g_state" in self.req.cookies and self.req.cookies.get("g_state", None)!='{':
            if "id_info" not in self.ses or not self.ses["id_info"]:
                return HTTPFound(location=self.req.route_url("base-login"))

        reg_form = BASE_CLASS.reg_form
        if reg_form != "base-register":
            return HTTPFound(location=self.req.route_url(reg_form))
        return super().view_add()

    def save_request(self, values, row=None):
        if not "email" in values or not values["email"]:
            values["email"] = self.req.user and self.req.user.email or ""

        if not row:
            values["is_vendor"] = 0
            values["is_customer"] = 1
        row = super().save_request(values, row)

    def after_save(self, values, row):
        # User Baru
        if not self.req.user:
            #todo: simplikasi lagi disini
            user = User()
            user.email = row.email
            user.user_name = row.email
            user.registered_date = datetime.now()
            self.db_session.add(user)
            self.db_session.flush()
            if 'groups' in values and values['groups']:
                gr = Group.query_group_name(values['groups']).first()
                ug = UserGroup()
                ug.user_id = user.id
                ug.group_id = gr.id
                self.db_session.add(ug)
                add_member_count(gr.id)
                self.db_session.flush()

            remain = regenerate_security_code(user)
            send_email_security_code(
                self.req, user, remain, 'Welcome new user', 'email-new-user',
                'email-new-user.tpl')
            ts = _(
                'user-added',
                default='${email} berhasil ditambahkan dan email untuk ubah '
                        'kata kunci sudah dikirim.',
                mapping={"email": row.email})
            self.ses.flash(ts)
        return super().after_save(values, row)
        return row

    def query_id(self):
        return DBSession.query(Partner). \
            filter(Partner.email == self.req.user.email)


#     def id_not_found(self, **kwargs):
#         return
    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        self.send_profile_password()
        partner = DBSession.query(Partner). \
            filter(Partner.email == self.req.user.email).first()
        if partner:
            fields = ["nama", "alamat_1", "alamat_2", "mobile", "email", "kode",
                      "idcard"]
            for f in fields:
                d[f] = hasattr(partner, f) and getattr(partner, f) or ""
            filename = d.get("idcard", "")
            d.pop("idcard")
            preview_url = "/".join(
                [self.req.static_url(BASE_CLASS.partner_doc),
                 filename])
            # if self.req.is_xhr: # Penambahan jika XHR tidak di parsing
            #     d["idcard"] = filename and preview_url or ""
            # else:
            if filename:
                d["idcard"] = {"uid": filename.split(".")[0],
                            "filename": filename,
                            "preview_url": preview_url
                            }
        return d

    # def before_add(self):

    def view_profile(self):
        self.buttons = (btn_save, btn_cancel)
        reg_form =BASE_CLASS.reg_form
        if reg_form and reg_form != "base-register":
            return HTTPFound(location=self.req.route_url(reg_form))
        
        self.bindings = dict(user=self.req.user)
        partner = Partner.query_email(self.req.user.email).first()
        if not partner:
            resp = super().view_add()
        else:
            resp = super().view_edit()
        return resp


"""
    def next_add(self, form, **kwargs):
        table = kwargs.get("table")
        kwargs.pop("table", None)
        resources = kwargs.get("resources")
        if 'register' in self.req.POST:
            controls = self.req.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                value = self.before_add()
                for f in e.field.children:
                    if isinstance(f.typ, colander.Date):
                        e.cstruct[f.name] = date_from_str(
                            e.cstruct[f.name])
                    if f.name == "captcha":
                        e.cstruct[f.name] = self.get_captcha_url()
                value.update(e.cstruct)
                form.set_appstruct(e.cstruct)
                return self.returned_form(form, table, **kwargs)

                #            js=resources["js"])
            values = dict(c)
            row = self.save_request(values)
            self.after_add(row=row, values=values)
        return self.route_list()
"""