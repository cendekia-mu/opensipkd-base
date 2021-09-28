import re
from datetime import datetime
from email.utils import parseaddr

import transaction
##################
# RPC USER
##################
from pyramid_rpc.jsonrpc import jsonrpc_method

from opensipkd.tools.api import (
    JsonRpcInvalidLoginError, JsonRpcInvalidNikError, JsonRpcInvalidMobileError,
    JsonRpcInvalidEmailError, JsonRpcUserFoundError, JsonRpcEmailFoundError,
    JsonRpcNikFoundError, JsonRpcRegisterFailError, JsonRpcInvalidDataError,
    JsonRpcUserNotFoundError, JsonRpcProfileFailError, JsonRpcMobileFoundError)
from .base_google import googlesignin
from .user import add_member_count
from .user import save_user
from .user_group import save as save_groups
from .. import get_params, log
from ..models import DBSession, UserService, Departemen
from ..models import (User, Partner, Group, UserGroup, PartnerDepartemen)
from opensipkd.tools import create_now, get_settings
from opensipkd.tools.api import custom_error
from opensipkd.base.tools.api import (
    auth_from_rpc, check_token_rpc, update_token)
from ..views.partner import save as save_partner


def insert_user(request, values):
    q = DBSession.query(Group).filter(Group.group_name.ilike('web service'))
    ws_group = q.first()
    user = User()
    user.email = values['email'].lower()
    user.user_name = values['user_name'].lower()
    user.password = values['password']
    user.status = 1
    DBSession.add(user)
    DBSession.flush()
    ug = UserGroup(user_id=user.id, group_id=ws_group.id)
    DBSession.add(ug)
    add_member_count(ws_group.id)
    return user


def get_user(data):
    user = 'user_name' in data and User.get_by_identity(data['user_name']) or None
    if not user:
        user = 'email' in data and User.get_by_identity(data['email']) or None

    if not user:
        log.info("Get User Rpc Not Found")
        raise JsonRpcUserNotFoundError
    return user


def get_user_token(row):
    user = 'token' in row and User.get_by_token(row['token']).first()
    return user


# def validasi_nik(nik):
#     return partner.query().filter_by(kode=nik).first()


def validasi_email(value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        return
    return True


def validasi_user(data, row=None):
    user = User.get_by_identity(data['user_name'])
    if (not row and user) or (row and user and row.id != user.id):
        log.info("Validasi User Found")
        raise JsonRpcUserFoundError

    user = User.get_by_identity(data['email'])
    if (not row and user) or (row and user and row.id != user.id):
        log.info("Validasi Email Found")
        raise JsonRpcEmailFoundError


def validasi_partner(data, row=None):
    # Cek di partner
    partner = Partner.query_email(data['email']).first()
    if (not row and partner) or (row and partner and row.id != partner.id):
        log.info("Validasi Email Found")
        raise JsonRpcEmailFoundError

    partner = Partner.query_kode(data['nik']).first()
    if (not row and partner) or (row and partner and row.id != partner.id):
        log.info("Validasi NIK Found")
        raise JsonRpcNikFoundError

    partner = Partner.query().filter_by(mobile=data['mobile']).first()
    if (not row and partner) or (row and partner and row.id != partner.id):
        log.info("Validasi Mobile Found")
        raise JsonRpcMobileFoundError


def validasi_data(dat):
    nik = ""
    if 'nik' in dat:
        nik = re.sub('\D', '', dat['nik'])
        if len(nik) != 16:
            log.info("Validasi NIK Error")
            raise JsonRpcInvalidNikError

    mobile = re.sub('\D', '', dat['mobile'])
    if len(mobile) < 9:
        log.info("Validasi Mobile Error")
        raise JsonRpcInvalidMobileError

    email = dat['email']
    if not validasi_email(email):
        log.info("Validasi Email")
        raise JsonRpcInvalidEmailError

    dat['nik'] = nik and nik or mobile
    dat['mobile'] = mobile
    dat['email'] = email
    return dat


def register_user_(data, user, groups=None):
    is_list = isinstance(data, list)
    if is_list:
        data_list = data
    else:
        data_list = [data]
    result = []
    for data in data_list:
        if not ('user_name' in data and 'password' in data and 'email' in data
                and 'nama' in data and 'mobile' in data):
            raise JsonRpcInvalidDataError

        data = validasi_data(data)
        validasi_user(data)
        data['status'] = 1
        row = save_user(data, user=user)
        if not row:
            raise JsonRpcRegisterFailError

        # proses ke tabel partner
        kode = 'nik' in data and data['nik'] or ""
        if not kode:
            kode = 'kode' in data and data['kode'] or ""

        if not kode:
            kode = 'email' in data and data['email'] or ""

        data['kode'] = kode
        data['user_id'] = row.id
        data['is_customer'] = 1
        user = row if not user else user
        validasi_partner(data)
        partner = save_partner(data, user)
        if not partner:
            transaction.abort()
            raise JsonRpcRegisterFailError

        ##Untuk SIMKEL##
        settings = get_settings()
        default_group = get_params("default_group")
        if default_group:
            groups = settings['default_group'].split(',')
            for group in groups:
                group_data = Group.query_group_name(group).first()
                if not group_data:
                    raise custom_error(-1, "Group Not Found.")
                data['group_id'] = group_data.id
                data['user_id'] = row.id
                save_groups(data, None)
        if not groups:
            raise Exception("Groups Kosong")
        ret_groups = []
        if groups:
            for group in groups.split(','):
                group_data = Group.query_group_name(group).first()
                if not group_data:
                    print(group)
                    raise Exception("Groups Data Kosong")

                if group_data:
                    data['group_id'] = group_data.id
                    data['user_id'] = row.id
                    row = save_groups(data, None)
                    ret_groups.append(dict(group_name=group))
                    del data['group_id']
                    del data['user_id']
            data['groups']=ret_groups
        result.append(data)

    if not is_list:
        result = result[0]
    return result


# url /rpc/user , permission='web-service'
@jsonrpc_method(method='register', endpoint='rpc-user')
def register_user(request, data, groups=''):
    # Digunakan untuk registrasi user via aplikasi lain
    # parameter user_name, password, email, nama, mobile, nik
    user = auth_from_rpc(request)
    result = register_user_(data, user, groups)
    return dict(message="Sukses Register User", data=result)


# 3 , permission='web-service'
def login_(request, data):
    is_list = type(data) is list
    data = is_list and data[0] or data
    row = get_user(data)
    if not row:
        if 'external' in data:
            from .base_google import googlesignin
            row = googlesignin(request)
            if not row:
                result = dict(next="complete_user",
                              message="Silahkan Melakukan Registrasi")
                raise JsonRpcInvalidLoginError(data=result)
        raise JsonRpcInvalidLoginError

    if not UserService.check_password(row, data['password']):
        raise JsonRpcInvalidLoginError

    row.last_login_date = create_now()
    DBSession.add(row)
    DBSession.flush()
    partner = Partner.query().filter_by(user_id=row.id).first()
    if not partner and row.id > 1:
        raise JsonRpcInvalidDataError(message="Silahkan melengkapi Registrasi")

    result = None
    if row.id == 1:
        is_pegawai = 1
    else:
        is_pegawai = partner and not partner.is_customer and not partner.is_vendor and 1 or 0

    ##RETURNING GROUP##
    groups = DBSession.query(Group). \
        join(UserGroup, UserGroup.group_id == Group.id). \
        filter(UserGroup.user_id == row.id).all()
    group_data = []
    for group in groups:
        group = group.to_dict()
        group_data.append(dict(group_name=group['group_name']))
    now = datetime.now().date()
    partner_dep = Departemen.query() \
        .join(PartnerDepartemen, Departemen.id == PartnerDepartemen.departemen_id) \
        .join(Partner, Partner.id == PartnerDepartemen.partner_id) \
        .filter(Partner.email == row.email,
                PartnerDepartemen.mulai <= now,
                PartnerDepartemen.selesai >= now).first()
    if partner_dep:
        departemen = dict(id=partner_dep.id,
                          kode=partner_dep.kode,
                          nama=partner_dep.nama)
    else:
        departemen = None

    result = dict(user_name=row.user_name,
                  token=row.security_code,
                  nik=partner and partner.kode or '',
                  nama=partner and partner.nama or '',
                  is_pegawai=is_pegawai,
                  group=group_data,
                  departemens=departemen)
    result = is_list and [result] or result
    return dict(data=result)


@jsonrpc_method(method='login', endpoint='rpc-user')
def login(request, data):
    # Digunakan untuk login dari aplikasi lain
    # parameter user_name/email, user_password
    ws_user = auth_from_rpc(request)
    return login_(request, data)


# , permission='web-service'
def get_profile_(user):
    # is_list = type(data) is list
    # dat = is_list and data[0] or data
    # user = get_user(data)
    # if not user or not UserService.check_password(user, data['password']):
    #     raise JsonRpcInvalidLoginError

    partner = Partner.query().filter_by(user_id=user.id).first()
    if not partner:
        raise JsonRpcInvalidDataError

    result = dict(user_name=user.user_name,
                  nik=partner.kode,
                  email=partner.email,
                  mobile=partner.mobile,
                  nama=partner.nama, )

    # result = is_list and [result] or result
    return dict(data=result)


@jsonrpc_method(method='get_profile', endpoint='rpc-user')
def get_profile(request, data):
    # Digunakan untuk memperoleh profile user
    # parameter user_name, password
    auth_from_rpc(request)
    user = get_user(data)
    if not user or not UserService.check_password(user, data['password']):
        raise JsonRpcInvalidLoginError
    return get_profile_(user)


# , permission='web-service'
def set_profile_(request, data):
    is_list = type(data) is list
    data = is_list and data[0] or data
    if not ('user_name' in data and 'password' in data and 'email' in data
            and 'nama' in data and 'mobile' in data and 'nik' in data):
        raise JsonRpcInvalidDataError

    data = validasi_data(data)
    if 'external' in data:
        user = googlesignin(request)
        if not user:
            raise JsonRpcInvalidLoginError

    else:
        user = get_user(data)
        if not UserService.check_password(user, data['password']):
            raise JsonRpcInvalidLoginError

        # if not user or UserService.check_password(user, data['password']):
        #     raise JsonRpcInvalidLoginError

    validasi_user(data, user)
    partner = Partner.query().filter_by(user_id=user.id).first()
    validasi_partner(data, partner)

    if 'new_password' in data:
        data['password'] = data['new_password']

    row = save_user(data, user, user)
    if not row:
        raise JsonRpcProfileFailError

    partner = save_partner(data, user, partner)
    if not partner:
        transaction.abort()
        raise JsonRpcProfileFailError

    result = data
    result = is_list and [result] or result
    return dict(message='Sukses Ubah', data=result)


@jsonrpc_method(method='set_profile', endpoint='rpc-user')
def set_profile(request, data):
    # Digunakan untuk menyimpan profile kepada aplikasi lain
    # parameter user_name / password
    return set_profile_(request, data)


def get_password_(request, data):
    identity = data['email']
    q = User.query_email(email=identity)
    user = q.first()
    if not user:
        raise JsonRpcUserNotFoundError

    from opensipkd.base.views.user_login import (
        regenerate_security_code, send_email_security_code)
    remain = regenerate_security_code(user)
    send_email_security_code(
        request, user, remain, 'Reset password', 'reset-password-body',
        'reset-password-body.tpl')
    return dict(data=dict(message='Email reset password sudah terkirim ke %s' % identity))


@jsonrpc_method(method='get_password', endpoint='rpc-user')
def get_password(request, data):
    auth_from_rpc(request)
    return get_password_(request, data)


def set_password_(token, data):
    user = check_token_rpc(token)
    if not UserService.check_password(user, data["password"]):
        raise JsonRpcInvalidLoginError

    if "new_password" in data and data["new_password"]:
        UserService.set_password(User, data["new_password"])

    result = dict(message="Sukses Ubah Password")
    result.update(update_token(user))
    return result


@jsonrpc_method(method='set_password', endpoint='rpc-user')
def set_password(request, token, data):
    auth_from_rpc(request)
    return set_password_(token, data)
