from datetime import datetime

import colander
from deform import Form, ValidationFailure
from opensipkd.base.tools.api import (
    get_user_device)
from opensipkd.base.views.partner_base import NamaSchema
from opensipkd.jsonrpc_auth import JsonRpcInvalidLogin
from opensipkd.tools import create_now
from opensipkd.tools.api import (
    JsonRpcInvalidLoginError, JsonRpcInvalidData,
    JsonRpcUserNotFoundError)
from pyramid.i18n import TranslationStringFactory
from pyramid.security import remember, forget
from pyramid_rpc.jsonrpc import jsonrpc_method

from .user import EmailValidator as EmailValidatorBase
from .user_group import save as save_groups
from .user_login import (ChangePassword, change_password_validator,
                         regenerate_security_code, send_email_security_code)
from opensipkd.models import DBSession, UserService, Departemen
from opensipkd.models import (User, Partner, Group, UserGroup, PartnerDepartemen)

_ = TranslationStringFactory('user')


def get_user(data):
    user = 'user_name' in data and User.get_by_identity(
        data['user_name']) or None
    if not user:
        user = 'email' in data and User.get_by_identity(data['email']) or None
    return user


def login_(request, data):
    user = get_user(data)
    if not user:
        if 'external' in data:
            from .base_google import googlesignin
            user = googlesignin(request)
            if not user:
                result = dict(next="complete_user",
                              message="Silahkan Melakukan Registrasi")
                raise JsonRpcInvalidLoginError(data=result)
        else:
            raise JsonRpcInvalidLoginError
    else:
        if not UserService.check_password(user, data['password']):
            raise JsonRpcInvalidLoginError

    user.last_login_date = create_now()
    DBSession.add(user)
    DBSession.flush()
    headers = remember(request, user.id)
    request.headers.update(headers)
    response = request.response
    response.headers.update(headers)
    groups = DBSession.query(Group). \
        join(UserGroup, UserGroup.group_id == Group.id). \
        filter(UserGroup.user_id == user.id).all()
    group_data = []
    for group in groups:
        group = group.to_dict()
        group_data.append(dict(group_name=group['group_name']))
    now = datetime.now()
    partner = Partner.query().filter_by(email=user.email).first()
    departemen = None
    if partner:
        partner_dep = Departemen.query() \
            .join(PartnerDepartemen,
                  Departemen.id == PartnerDepartemen.departemen_id) \
            .join(Partner, Partner.id == PartnerDepartemen.partner_id) \
            .filter(Partner.email == user.email,
                    PartnerDepartemen.mulai <= now,
                    PartnerDepartemen.selesai >= now).first()
        if partner_dep:
            departemen = dict(id=partner_dep.id,
                              kode=partner_dep.kode,
                              nama=partner_dep.nama)

    return dict(id=user.id,
                user_name=user.user_name,
                nik=partner and partner.kode or '',
                nama=partner and partner.nama or '',
                group=group_data,
                departemens=departemen)


@jsonrpc_method(method='login', endpoint='rpc-user')
def login(request, data):
    """
    Digunakan untuk login pada aplikasi lain
    :param request:
    :param data:
    {
        "user_name": "user_name",
        "password": "password"
    }
    :return:
        result: "data":
        {
            "user_name": "user_name",
            "nik": nik,
            "nama": nik,
            "group": [group],
            "departemens": [departemen]
        }
        error:"error":{}
    """
    is_list = type(data) is list
    data = is_list and data[0] or data
    resp = login_(request, data)
    # resp["token"] = get_user_device(request, resp["id"]).token
    result = is_list and [resp] or resp
    return result


@jsonrpc_method(method='logout', endpoint='rpc-user', permission="view")
def logout(request, data):
    """
    Digunakan untuk login pada aplikasi lain
    :param request:
    :param data:
    {
    }
    :return:{
    }
    """
    headers = forget(request)
    request.session.delete()
    request.response.headers.update(headers)
    return dict(data="")


def get_profile_(user):
    partner = Partner.query().filter_by(email=user.email).first()
    if not partner:
        return dict(user_name=user.user_name,
                    nik="",
                    email="",
                    mobile="",
                    nama="", )

    return dict(user_name=user.user_name,
                nik=partner.kode,
                email=partner.email,
                mobile=partner.mobile,
                nama=partner.nama, )

@jsonrpc_method(method='get-profile', endpoint='rpc-user', permission="view")
@jsonrpc_method(method='get_profile', endpoint='rpc-user', permission="view")
def get_profile(request, data):
    """
    Digunakan untuk memperoleh profile user yang sedang login
    parameter
    @param request: Request
    @param data: {"password": password}
    @return:
    """
    user = request.request.user
    is_list = type(data) == list
    data = is_list and data[0] or data
    if not user or not UserService.check_password(user, data['password']):
        raise JsonRpcInvalidLoginError

    resp = get_profile_(user)
    resp = is_list and [resp] or resp
    return resp


class EmailValidator(EmailValidatorBase):
    def __call__(self, node, value):
        def email_found_partner():
            data = dict(email=email, uid=found.id)
            ts = _(
                'email-already-used',
                default='Email ${email} already used by partner ID ${uid}',
                mapping=data)
            raise colander.Invalid(node, ts)

        super().__call__(node, value)

        email = value.lower()
        q = DBSession.query(Partner).filter_by(email=email)
        found = q.first()
        if found and (not self.user or self.user.email != found.email):
            email_found_partner()


@colander.deferred
def email_validator(node, kw):
    return EmailValidator(kw['user'])


class PartnerSchema(NamaSchema):
    email = colander.SchemaNode(
        colander.String(),
        validator=email_validator
    )
    mobile = colander.SchemaNode(
        colander.String()
    )


def form_validator(form, values):
    exc = colander.Invalid(form, "")
    user = form.request.user
    if user:
        values["update_uid"] = user.id
        values["updated"] = datetime.now()
    else:
        values["create_uid"] = user.id
        values["created"] = datetime.now()

    values["is_customer"] = "is_customer" in values and values[
        "is_customer"] or 1
    values["is_vendor"] = "is_vendor" in values and values["is_vendor"] or 0
    mobile = values["mobile"]
    partner = Partner.query().filter_by(mobile=mobile).first()
    if partner:
        if not user or user and user.email != partner.email:
            exc["mobile"] = "No Handphone sudah ada yang menggunakan"
            raise exc


def set_profile_(request, data):
    schema = PartnerSchema(validator=form_validator)
    schema = schema.bind(request=request, user=request.user)
    schema.request = request
    form = Form(schema)
    data["kode"] = data["nik"]
    controls = ((k, v) for k, v in data.items())
    try:
        controls = form.validate(controls)
    except ValidationFailure as e:
        print(e.error, type(e.error))
        raise JsonRpcInvalidData(data=e.error.asdict())
    values = dict(controls)
    partner = Partner.query().filter_by(email=values["email"]).first()
    if not partner:
        partner = Partner()
    partner.from_dict(values)
    DBSession.add(partner)
    DBSession.flush()
    return values


@jsonrpc_method(method='set-profile', endpoint='rpc-user', permission="view")
@jsonrpc_method(method='set_profile', endpoint='rpc-user', permission="view")
def set_profile(request, data):
    """
    Digunakan untuk menyimpan profile
    :param request:
    :param data:Dict(
        nik="",
        email="",
        mobile="",
        nama="",
        alamat_1="",
        alamat_2=""
    )
    :return:
    """
    is_list = type(data) is list
    data = is_list and data[0] or data
    user = request.user
    if not UserService.check_password(user, data['password']):
        raise JsonRpcInvalidLoginError

    old_email = user.email
    values = set_profile_(request, data)
    user.from_dict(values)
    if old_email != data["email"]:
        remain = regenerate_security_code(user)
        send_email_security_code(
            request, user, remain, 'Change email', 'change-email-body',
            'change-email-body.tpl')
        user.status = 0
        headers = forget(request)
        request.session.delete()
        request.response.headers.update(headers)
        return dict(message=f"Silahkan buka email {old_email}")

    return dict(message="Sukses Ubah Profile")


@jsonrpc_method(method='register', endpoint='rpc-user')
def register_user(request, data):
    """
    Digunakan untuk registrasi user dan profile
    :param request:
    :param data:{
        "user_name"="",
        "email"="",
        "mobile"="",
        "nama"="",
        "alamat_1"="",
        "alamat_2"=""
    }
    :return:
    """
    is_list = type(data) is list
    data = is_list and data[0] or data
    values = set_profile_(request, data)
    user = User()
    user.from_dict(values)
    DBSession.add(user)
    DBSession.flush()
    groups = data["groups"]
    for g in groups:
        d = Group.query_group_name(g).first()
        data['group_id'] = d.id
        data['user_id'] = user.id
        save_groups(data, None)

    remain = regenerate_security_code(user)
    send_email_security_code(
        request, user, remain, 'Welcome new user', 'email-new-user',
        'email-new-user.tpl')
    ts = _(
        'user-added',
        default='${email} berhasil ditambahkan dan email untuk ubah ' \
                'kata kunci sudah dikirim.',
        mapping=data)
    return dict(message=ts)


def get_password_(request, data):
    identity = data['email']
    q = User.query_email(email=identity)
    user = q.first()
    if not user:
        raise JsonRpcUserNotFoundError

    remain = regenerate_security_code(user)
    send_email_security_code(
        request, user, remain, 'Reset password', 'reset-password-body',
        'reset-password-body.tpl')
    return dict(data=dict(
        message='Email reset password sudah terkirim ke %s' % identity))


@jsonrpc_method(method='get-password', endpoint='rpc-user')
@jsonrpc_method(method='get_password', endpoint='rpc-user')
def get_password(request, data):
    """
    Digunakan untuk request password
    :param request:
    :param data: {
        "email": email
        }
    :return:
        success: {"result": {}}
        error: {"error": {}}
    """
    return get_password_(request, data)


def set_password_(user, data):
    schema = ChangePassword(validator=change_password_validator)
    form = Form(schema)
    items = ((k, v) for k, v in data.items())
    try:
        c = form.validate(items)
    except ValidationFailure as e:
        raise JsonRpcInvalidLogin(data=e.error.asdict())

    UserService.set_password(user, c['new_password'])
    DBSession.add(user)
    DBSession.flush()
    if "new_password" in data and data["new_password"]:
        UserService.set_password(User, data["new_password"])

    result = dict(message="Sukses Ubah Password")
    return result


@jsonrpc_method(method='set-password', endpoint='rpc-user', permission="view")
@jsonrpc_method(method='set_password', endpoint='rpc-user', permission="view")
def set_password(request, data):
    """
    Digunakan untuk mengubah password
    :param request:
    :param data: {
        "password": old_password,
        "new_password": new_password,
        "retype_password": conf_password,
        }
    :return:
        success: {"result": {}}
        error: {"error": {}}
    """
    user = request.user
    is_list = type(data) is list
    data = is_list and data[0] or data
    resp = set_password_(user, data)
    headers = forget(request)
    request.session.delete()
    request.response.headers.update(headers)
    return resp
