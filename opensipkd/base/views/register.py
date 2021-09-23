from datetime import (datetime)
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from ..views import BaseView
import colander
from deform import (Form, widget, ValidationFailure, Button)
from email.utils import parseaddr
from ..models import User, DBSession, Partner, Group, UserGroup
from opensipkd.base.views.user_login import send_email_security_code
from opensipkd.base.views.user import insert as save_user, add_member_count
from pyramid.i18n import TranslationStringFactory
from opensipkd.tools import get_settings
from opensipkd.tools.captcha import get_captcha
from ziggurat_foundations.models.services.user import UserService
from .user_group import save as save_groups
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


class RegSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=18, max_err='Maximum ${max} Digit',
                                  min=15, min_err='Minimimum ${min} Digit'),
        title="No.Identitas/NIK",
        oid="kode")
    detail = NamaSchema()
    captcha = colander.SchemaNode(
        colander.String(),
        oid="captcha")


class RegEditSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(readonly=True),
        missing=colander.drop,
        title="NIK",
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


def email_found_user(email):
    return User.get_by_identity(email)


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

    def err_captcha():
        msg = 'Captcha harus diisi'
        raise colander.Invalid(form, msg)

    def err_email():
        raise colander.Invalid(
            form, 'e-mail %s sudah ada yang menggunakan' % value['email'])

    def err_nik():
        raise colander.Invalid(
            form, 'NIK %s sudah ada yang menggunakan' % value['kode'])

    def err_login():
        raise colander.Invalid(
            form, 'User atau Password tidak sesuai')

    request = form.request
    # Cek Login
    if 'password' in value:
        user = form.request.user
        if not user or not UserService.check_password(user, value['password']):
            err_login()

    if not request.user:
        if 'captcha' not in value or not value['captcha'] \
                or 'captcha' not in request.session or not request.session['captcha']:
            err_captcha()

        captcha = 'captcha' in value and value['captcha'].upper() or None

        if not captcha or captcha != request.session['captcha']:
            err_captcha()

    if 'id' in request.matchdict:
        uid = request.matchdict['id']
        q = DBSession.query(Partner).filter_by(id=uid)
        partner = q.first()
    else:
        partner = None
    detail = value['detail']
    email = detail['email']

    found = email_found_partner(email)
    if partner:
        if found and found.id != partner.id:
            err_email()
    elif found:
        err_email()

    # CEK NIK apakah Sudah Ada di tabel Partner?
    if not partner:
        found_nik = nik_found(value['kode'])
        if partner:
            if found_nik and found_nik.id != partner.id:
                err_nik()
        elif found_nik:
            err_nik()

    user = email_found_user(email)
    # jika ada user dan statusnya register di buat error
    if user and not form.request.user:
        err_email()

    # jika update periksa apakah email digunakan oleh user lain
    if user and form.request.user:
        if user.id != form.request.user.id:
            err_email()


def get_form(request, class_form, buttons=None, validator=form_validator):
    schema = class_form(validator=validator)
    schema = schema.bind()
    schema.request = request
    if buttons:
        return Form(schema, buttons=buttons)
    return Form(schema, buttons=('batal', 'simpan'))


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
        user_ = dict(user_name=values['nama'],
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
                default='${email} berhasil ditambahkan dan email untuk ubah '\
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
    settings = get_settings()
    if 'default_group'in settings:
        groups = settings['default_group'].split(',')
        for group in groups:
            group_data = Group.query_group_name(group).first()
            if not group_data:
                raise custom_error(-1,"Group Not Found.")
            data = dict(group_id = group_data.id,
                        user_id = user.id)
            save_groups(data,None)
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
            partner = Partner.query_user_id(request.user.id).first()
            if partner:
                return HTTPFound(location=request.route_url("profile", id=partner.id))

        form = get_form(request, RegSchema, reg_buttons())
        if request.POST:
            if 'register' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form, captcha=get_captcha(request))

                save_request(dict(controls), request)
                request.session.flash('Registrasi Sukses.')

                if 'captcha' in request.session:
                    del(request.session['captcha'])

            return route_list(request)
        values = {}
        if request.user:
            values['email'] = request.user.email

        form.set_appstruct(values)
        return dict(form=form, captcha=get_captcha(request))

    @view_config(route_name='profile', renderer='templates/register-edt.pt',
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
            values = dict(email=request.user.email)

        form.set_appstruct(values)
        return dict(form=form)


########
# Edit #
########
def query_id(request):

    return DBSession.query(Partner).\
        join(User, Partner.user_id == User.id).\
        filter(User.id == request.user.id)


def id_not_found(request):
    msg = 'Register ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
