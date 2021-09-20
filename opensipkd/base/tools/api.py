import json
import requests
from opensipkd.tools import (
    get_random_number, devel, get_random_string, get_settings)
from opensipkd.tools.api import *
from .. import log
from ..models import (DBSession, User, GroupPermission)

lima_menit = 300
def auth_from_rpc(request):
   return auth_from(request)

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
    if http_userid == 'admin' and request.devel:
        return user

    time_stamp = int(env['HTTP_KEY'])
    now = get_seconds()
    settings = get_settings()
    if 'diff_server_time' in settings and settings["diff_server_time"]:
        lima_menit = int(settings["diff_server_time"])

    if not request.devel and abs(now - time_stamp) > lima_menit:
        raise JsonRpcInvalidTimeError
    if field:
        header = json_rpc_header(http_userid, user.security_code, time_stamp)
    else:
        header = json_rpc_header(http_userid, user.api_key, time_stamp)

    if header['signature'] != env['HTTP_SIGNATURE']:
        raise JsonRpcInvalidLoginError

    return user


def auth_from_token(request):
    return auth_from(request, "security_code")


def get_jsonrpc(method, params):
    return dict(jsonrpc='2.0', method=method, params=params,
                id=int(get_random_number(6)))


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


def get_mandatory(data, values):
    for value in values:
        if value not in data or not data[value]:
            raise JsonRpcInvalidDataError(message="{} Not Found".format(value))


def send_rpc(auth, message):
    """
    Digunakan untuk mengirim data dengan methode JSONRPC 2.0 with os-auth
    :param auth: Dict
        {"user": user,
        "url": url,
        "key": key,
        "method": method,
        "timeout": optional,
        }
    :param message: Dict
    :return: Dict
    """
    userid = auth['user']
    password = auth['key']
    url = auth['url']
    headers = json_rpc_header(userid, password)
    params = dict(data=message)
    data = get_jsonrpc(auth["method"], params)
    timeout = 'timeout' in auth and int(auth['timeout']) or 5
    log.info("URL:{} timeout:{} detik".format(url, timeout))
    log.warning("REQUEST {}".format(data))
    try:
        results = requests.post(url, json=data, headers=headers, timeout=timeout)  # data=jsondata,
    except Exception as e:
        log.warning(str(e))
        return
    if results.status_code != 200:
        log.info(results)
        log.info(results.text)
        return
    rows = results.text and json.loads(results.text) or None
    log.info("RESPONSE {}".format(rows))
    return rows
