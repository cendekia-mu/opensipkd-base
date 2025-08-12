from opensipkd.base import get_params
from opensipkd.base.models import (DBSession, User, GroupPermission, UserDeviceModel)

from opensipkd.tools import (
    devel, get_random_string)
from opensipkd.tools.api import *

log = logging.getLogger(__name__)

lima_menit = 300


def auth_from(request, field=None):
    global lima_menit
    env = request.environ
    log.info(env)
    if not ('HTTP_USERID' in env and 'HTTP_SIGNATURE' in env and
            'HTTP_KEY' in env):
        raise JsonRpcInvalidLoginError

    http_userid = env['HTTP_USERID']
    q = DBSession.query(User).filter_by(user_name=http_userid)
    user = q.first()

    if not user or user.status == 0:
        raise JsonRpcInvalidLoginError

    # bypass cek authentication for development
    if http_userid == 'admin' and log.parent.level==logging.DEBUG:
        return user

    time_stamp = validate_time(request)
    if field:
        header = json_rpc_header(http_userid, user.security_code, time_stamp)
    else:
        header = json_rpc_header(http_userid, user.api_key, time_stamp)

    if header['signature'] != env['HTTP_SIGNATURE']:
        raise JsonRpcInvalidLoginError

    return user

def auth_from_rpc(request):
    return auth_from(request)

def rpc_auth(request):
    return auth_from(request)



# def auth_from_token(request):
#     return auth_from(request, "security_code")
#

# def renew_token(user_device, logout=False):
#     now = datetime.now(tz=get_timezone())
#     tte = timedelta(minutes=10)
#     if not user_device.expired or not user_device.token or \
#             now - user_device.expired > tte:
#         user_device.expired = now
#         user_device.token = get_random_string(128)
#     if logout:
#         user_device.token=""
#     DBSession.add(user_device)
#     DBSession.flush()
#     return user_device

# def token_auth(request, logout=False):
    # if not request.environ["HTTP_TOKEN"]:
    #     raise JsonRpcInvalidLoginError

    # user_device = UserDeviceModel.query() \
    #     .filter_by(kode=request.environ["HTTP_USER_AGENT"],
    #                token=request.environ["HTTP_TOKEN"]).first()
    # if not user_device:
    #     raise JsonRpcInvalidLoginError
    #
    # return renew_token(user_device, logout=logout)

def get_user_device(request, user_id):
    user_device = UserDeviceModel.query() \
        .filter_by(user_id=user_id,
                   kode=request.environ["HTTP_USER_AGENT"]).first()
    if not user_device:
        user_device = UserDeviceModel()
        user_device.user_id = user_id
        user_device.kode = request.environ["HTTP_USER_AGENT"]
    # user_device = renew_token(user_device)
    return user_device

def auth_device(request):
    env = request.environ
    log.info(env)
    if not ('HTTP_USERID' in env and 'HTTP_SIGNATURE' in env and
            'HTTP_KEY' in env):
        raise JsonRpcInvalidLoginError

    http_userid = env['HTTP_USERID']
    q = DBSession.query(User).filter_by(user_name=http_userid)
    user = q.first()

    if not user or user.status == 0:
        raise JsonRpcInvalidLoginError

    if http_userid == 'admin' and log.parent.level==logging.DEBUG:
        return user

    user_device = get_user_device(request, user)
    time_stamp = validate_time(request)
    header = json_rpc_header(http_userid, user_device.token, time_stamp)
    if header['signature'] != env['HTTP_SIGNATURE']:
        log.info(f"{http_userid}, {user_device.token}, {time_stamp}")
        log.info(f"{header['signature']} != {env['HTTP_SIGNATURE']}")
        raise JsonRpcInvalidLoginError

    return user



def check_token(token, perm_name=None):
    user = User.get_by_token(token).first()
    if not user:
        raise JsonRpcInvalidLoginError

    if not perm_name:
        return user

    groups = user.get_groups()
    perm = DBSession.query(GroupPermission). \
        filter(GroupPermission.group_id.in_(groups),
               GroupPermission.perm_name == perm_name).first()
    if not perm:
        return
    return user


def check_token_rpc(token, perm_name=None):
    result = check_token(token, perm_name)
    if not result:
        raise JsonRpcPermissionError
    return result


def update_token(user):
    if not devel():
        user.security_code = get_random_string(64)
        DBSession.add(user)
        DBSession.flush()
    return dict(token=user.security_code)

def config_pars_rpc_url(params, method=None):
    values = get_params(params)
    return pars_rpc_url(values, method)