import locale
import logging
import re

import colander

try:
    from urllib import (urlencode, quote, quote_plus, )
except ImportError:
    from urllib.parse import (urlencode, quote, quote_plus, )
from pyramid.events import NewRequest
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.renderers import JSON
from pyramid_mailer import mailer_factory_from_settings
import datetime, decimal
from sqlalchemy import engine_from_config, or_
from .security import (
    group_finder,
    get_user, MySecurityPolicy,
)
from opensipkd.models import (
    DBSession,
    Base,
    init_model,
    Route,
    Parameter)
from opensipkd.tools import (
    DefaultTimeZone,
    money,
    should_int,
    thousand,
    as_timezone,
    split,
    get_settings,
    dmy, dmyhms,
)

from deform import ZPTRendererFactory, Form
from pkg_resources import resource_filename

import os

from opensipkd.models.handlers import LogDBSession

log = logging.getLogger(__name__)

# version 2.0.0 digunakan untuk change default template
deform_templates = resource_filename('deform', 'templates')
path = os.path.dirname(__file__)
path = os.path.join(path, 'views', 'widgets')
search_path = (path, deform_templates)  # ,
renderer = ZPTRendererFactory(search_path)
Form.set_zpt_renderer(search_path)
main_title = 'openSIPKD'
titles = {}


# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true
# class RemoveSlashNotFoundViewFactory(object):
#     diganti menggunakan @view_config(context=HTTPNotFound, renderer='templates/404.pt') pada base.views
#     def __init__(self, notfound_view=None):
#         if notfound_view is None:
#             notfound_view = default_exceptionresponse_view
#         self.notfound_view = notfound_view
#
#     def __call__(self, context, request):
#         if not isinstance(context, Exception):
#             # backwards compat for an append_notslash_view registered via
#             # config.set_notfound_view instead of as a proper exception view
#             context = getattr(request, 'exception', None) or context
#         path_req = request.path
#         registry = request.registry
#         mapper = registry.queryUtility(IRoutesMapper)
#         if mapper is not None and path_req.endswith('/'):
#             noslash_path = path_req.rstrip('/')
#             for route in mapper.get_routes():
#                 if route.match(noslash_path) is not None:
#                     qs = request.query_string
#                     if qs:
#                         noslash_path += '?' + qs
#                     return HTTPFound(location=noslash_path)
#         return self.notfound_view(context, request)

def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        origin = request.headers.get("Origin", None)
        allowed_origin = get_params("allowed_origin", None)
        if allowed_origin:
            if origin not in allowed_origin.split('\n'):
                origin = None

        headers = {
            # 'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '1728000',
        }
        log.info(f"{origin} {request.is_xhr}")
        # response.headers.update(
        #     {'Access-Control-Allow-Credential': 'true',
        #      'Access-Control-Allow-Origin': "*"}
        # )
        if origin:
            headers['Access-Control-Allow-Origin'] = origin
        else:
            headers['Access-Control-Allow-Origin'] = "*"

        log.info(f"Headers: {headers}")
        response.headers.update(headers)

    event.request.add_response_callback(cors_headers)


# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, perm_names, context=None):
    if isinstance(perm_names, str):
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name, context):
            return True


def has_modules_(module_name, context=None):
    modules = get_params("pyramid.includes").split("\n")
    return module_name in modules


def _get_params(request, params, default=None, settings=None, context=None):
    return get_params(params, default, settings)


@subscriber(BeforeRender)
def add_global(event):
    event['has_permission'] = has_permission_
    event['has_modules'] = has_modules_
    event['urlencode'] = urlencode
    event['quote_plus'] = quote_plus
    event['quote'] = quote
    event['money'] = money
    event['should_int'] = should_int
    event['thousand'] = thousand
    event['as_timezone'] = as_timezone
    event['split'] = split
    event['allow_register'] = allow_register
    event['change_unit'] = change_unit
    event['get_params'] = get_params


def get_params(params, alternate=None, settings=None):
    """
    Digunakan untuk mengambil nilai dari konfigurasi sesuai params yang disebut
    :param params: variable
    :param alternate: default apabila tidak ditemukan data/params
    :param settings: default settings
    :return: value
    contoh penggunaan:
        get_params('devel', False)
    """

    if not settings:
        settings = get_settings()
    result = settings and params in settings and \
             settings[params].strip() or None
    if not result:
        row = Parameter.query_kode(params).first()
        result = row and row.value or None

    return result and result or alternate


def get_ini(request, var):
    settings = get_settings()
    if var in settings and settings[var]:
        return settings[var]
    return


def get_ini_params(request, params=None, alternate=None, settings=None):
    """
    Digunakan untuk mengambil nilai dari konfigurasi sesuai params yang disebut
    :param params: variable
    :param alternate: default apabila tidak ditemukan data/params
    :param settings: default settings
    :return: value
    contoh penggunaan:
        get_params('devel', False)
    """
    return get_params(params, alternate, settings)


def get_id_card_folder(ext=None):
    folder = get_params("partner_idcard_folder", '/tmp/idcard')
    if ext:
        return folder + ext
    return folder


def allow_register(request):
    allow = get_params('allow_register', 'false')
    return allow == 'true' or allow == "True" or allow == True


def disable_responsive(request):
    if get_params('disable_responsive') == 'true':
        return False
    return True


def change_unit(request):
    return get_params('change_unit') == 'true'


def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]


def get_company(request):
    return get_params('company', 'openSIPKD').upper()


def get_departement(request):
    return get_params('departement', 'DEPARTEMEN INFORMATION TEKNOLOGI').upper()


def get_ibukota(request):
    return get_params('ibukota', 'BEKASI')


def get_address(request):
    return get_params('address_1', 'ALAMAT DEPARTEMEN BARIS 1')


def get_address2(request):
    return get_params('address_2', 'ALAMAT DEPARTEMEN BARIS 2')


def get_app_name(request):
    return get_params('app_name', 'openSIPKD Application')


def is_devel(request):
    return get_params('devel') == 'true'


def google_signin_client_ids(request):
    ids = get_params('google-signin-client-id', '')
    if ids:
        return ids.split(',')
    else:
        return []


def google_signin_client_id(request):
    ids = google_signin_client_ids(request)
    if ids:
        return ids[0].strip()
    return ''


def get_modules(settings=None):
    # Digunakan untuk membaca module yang di setting pada ini file
    # Input berupa setting parameter
    # Result berupa dictionary key, value
    setting = get_settings()
    if not setting:
        setting = settings

    settings = setting
    modules = 'modules' in settings and settings['modules'] and settings[
        'modules'].split(',') or []
    result = {}
    for modul in modules:
        if not 'opensipkd.base' in modul:
            if modul.find(':') > -1:
                key, val = modul.strip().split(':')
            else:
                key = modul.strip()
                val = key.replace('opensipkd.', '')
                val = re.sub('[.//]', '-', val)
            result[key] = val.upper()
    return result


def get_menus(request):
    """
    digunakan untuk mengambil daftar menu untuk setiap modul yg sudah diregistrasikan di config key "menus".
    tadinaya akan dibuat didalam method get_modules,
    dikarenakan method get_modules lebih cenderung digunakan untuk meng-load module yang diregistrasikan di config key "modules",
    maka akan lebih aman dipisahkan antara pembacaan module dan menu.
    tetapi jika key "menus" kosong, maka secara default mengambil dari daftar modul.

    result sama dengan result module
    result = {
        url: title
    }
    """

    # settings = get_settings()
    # menus = 'menus' in settings and settings['menus'] and settings['menus'].split(',') or []
    menus = get_params('menus')
    menus = menus and menus.split('\n') or []
    if not menus:
        return get_modules(get_settings())

    result = {}
    for menu in menus:
        if menu.find(',') > -1:
            key, val = menu.strip().split(',')
            key = key.strip().strip('/')
            val = re.sub('[//-]', ' ', val)

        elif menu.find(':') > -1:
            key, val = menu.strip().split(':')
            key = key.strip().strip('/')
            val = re.sub('[//-]', ' ', val)
        else:
            key = menu.strip()
            val = key.replace('/', '-')
        if key and val:
            result[key] = val.upper()

        # HIDE CORE ##
        # untuk risti
        # if 'group_for_admin' in settings and settings['group_for_admin'] \
        #         and 'core' in menu:
        #     groups = request.user and request.user.groups or None
        #     groupes = []
        #     if groups:
        #         for group in groups:
        #             groupes.append(group.group_name)
        #     admin = settings['group_for_admin'].split(',')
        #     admin_match = 0
        #     for adm in admin:
        #         if adm in groupes:
        #             admin_match += 1
        #     if request.user and request.user.id == 1:
        #         admin_match += 1
        #     if 'core' in result and admin_match == 0:
        #         del result['core']
        # # selain risti
        # elif request.user and request.user.groups:
        #     if not request.has_permission('core'):
        #         if 'core' in result:
        #             del result['core']

    return result


def format_datetime(v):
    if v.time() != datetime.time(0, 0):
        return dmyhms(v)
    else:
        return dmy(v)


def json_renderer():
    json_r = JSON()
    json_r.add_adapter(datetime.datetime, lambda v, request: format_datetime(v))
    json_r.add_adapter(datetime.date, lambda v, request: dmy(v))
    json_r.add_adapter(decimal.Decimal, lambda v, request: str(v))
    return json_r


def json_rpc():
    json_r = JSON()
    json_r.add_adapter(datetime.datetime, lambda v, request: v.isoformat())
    json_r.add_adapter(datetime.date, lambda v, request: v.isoformat())
    json_r.add_adapter(decimal.Decimal, lambda v, request: str(v))
    return json_r


# class MyAuthenticationPolicy(AuthTktAuthenticationPolicy):
#     def authenticated_userid(self, request):
#         user = request.user
#         if user is not None:
#             return user.id


def get_host(request):
    host = get_params('_host', "")
    # if not host:
    #     host = request.route_url('home')[:-1]
    #     proto = 'HTTP_X_FORWARDED_PROTO' in request.environ \
    #             and request.environ['HTTP_X_FORWARDED_PROTO'] \
    #             or "http"
    #     host = f"{proto}://{request.host}"
    return host and host or get_home(request)


def get_home(request):
    return request.route_url('home')[:-1]


def set_routes(config, app_id=None):
    q = DBSession.query(Route)
    if not app_id:
        q.filter(or_(Route.app_id == 0, None == Route.app_id))
    else:
        q.filter(Route.app_id == app_id)

    for route in q:
        if route.type == 0:
            config.add_route(route.kode, route.path)
            if route.nama:
                titles[route.kode] = route.nama
        elif route.type == 1:
            config.add_jsonrpc_endpoint(route.kode, route.path,
                                        default_renderer="json_rpc")


partner_idcard_url = 'partner/idcard'


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    LogDBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'

    locale.setlocale(locale.LC_ALL, settings['localization'])
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone

    config = Configurator(settings=settings,
                          root_factory='opensipkd.models.RootFactory',
                          session_factory=session_factory)
    modules = get_modules(settings)
    from importlib import import_module
    for module in modules:
        # compatibility
        if module == 'admin':
            continue
        module = module.replace('/', '.')
        mfile = module
        m = import_module(mfile)
        cfg = m.main(config, **settings)
        if cfg:
            config = cfg

    config.set_security_policy(MySecurityPolicy(settings["session.secret"]))
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)

    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_request_method(get_company, 'company', reify=True)
    config.add_request_method(get_departement, 'departement', reify=True)
    config.add_request_method(get_ibukota, 'ibukota', reify=True)
    config.add_request_method(get_address, 'address', reify=True)
    config.add_request_method(get_address2, 'address2', reify=True)
    config.add_request_method(get_app_name, 'app_name', reify=True)
    config.add_request_method(get_modules, 'modules', reify=True)
    config.add_request_method(has_modules_, 'has_modules', reify=True)
    config.add_request_method(get_menus, 'menus', reify=True)
    config.add_request_method(thousand, 'thousand', reify=True)
    config.add_request_method(is_devel, 'devel', reify=True)
    config.add_request_method(get_host, '_host', reify=True)
    config.add_request_method(get_home, 'home', reify=True)
    config.add_request_method(google_signin_client_id,
                              'google_signin_client_id', reify=True)
    config.add_request_method(google_signin_client_ids,
                              'google_signin_client_ids', reify=True)
    config.add_request_method(allow_register, 'allow_register', reify=True)
    config.add_request_method(disable_responsive, 'disable_responsive',
                              reify=True)
    config.add_request_method(get_ini, 'get_ini', reify=True)
    config.add_translation_dirs('opensipkd.base:locale/')

    config.add_static_view('static', 'opensipkd.base:static',
                           cache_max_age=3600)
    config.add_static_view(partner_idcard_url,
                           get_id_card_folder("/"),
                           cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')

    captcha_files = get_params('captcha_files', settings=settings,
                               alternate="/tmp/captcha")
    if not os.path.exists(captcha_files):
        os.makedirs(captcha_files)

    config.add_static_view('captcha', captcha_files)
    config.add_renderer('csv', 'opensipkd.tools.CSVRenderer')
    config.add_renderer('json', json_renderer())
    config.add_renderer('json_rpc', json_rpc())
    set_routes(config)
    config.registry['mailer'] = mailer_factory_from_settings(settings)
    config.scan()
    for m in modules:
        config.scan(m)

    return config.make_wsgi_app()
