import importlib
import inspect
import locale
import logging
import re

from .routes import routes

# from opensipkd.tools.captcha import get_captcha_url

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
import datetime
import decimal
from sqlalchemy import engine_from_config, or_
from .security import (
    group_finder, get_user, MySecurityPolicy,)
from pyramid.csrf import get_csrf_token
from opensipkd.models import (
    DBSession, Base, Route, Parameter, init_model,)
from opensipkd.tools import (
    DefaultTimeZone, money, should_int, thousand, as_timezone, split,
    get_settings, dmy, dmyhms,)

from deform import ZPTRendererFactory, Form
from pkg_resources import resource_filename
from deform.widget import default_resource_registry
import os

from opensipkd.models.handlers import LogDBSession

_logging = logging.getLogger(__name__)

# version 2.0.0 digunakan untuk change default template
deform_templates = resource_filename('deform', 'templates')
path = os.path.dirname(__file__)
path = os.path.join(path, 'views', 'widgets')
search_path = (path, deform_templates)  # ,
renderer = ZPTRendererFactory(search_path)
Form.set_zpt_renderer(search_path)
main_title = 'openSIPKD'
titles = {}
static_route = []


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
                origin = "null"

        headers = {
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Max-Age': '1728000',
        }
        # _logging.info(f"{origin} {request.is_xhr}")
        # response.headers.update(
        #     {'Access-Control-Allow-Credential': 'true',
        #      'Access-Control-Allow-Origin': "*"}
        # )
        if origin:
            headers['Access-Control-Allow-Origin'] = origin
        else:
            headers['Access-Control-Allow-Origin'] = "*"
        if 'Access-Control-Allow-Credentials' not in headers:
            headers['Access-Control-Allow-Credentials'] = 'true'

        # _logging.info(f"Headers: {headers}")
        response.headers.update(headers)

    event.request.add_response_callback(cors_headers)


# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, perm_names, context=None):
    if not perm_names:
        return False
    if isinstance(perm_names, str):
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name, context):
            return True


def has_modules_(module_name, context=None):
    modules = get_params("pyramid.includes").split("\n")
    return module_name in modules


def _get_params(request, params, default=None, settings=None, context=None):
    _logging.debug(f"_get_params: {params}, {default}")
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    _logging.debug('caller name:', calframe[1][3])

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
    event['get_urls'] = get_urls
    event['get_csrf_token'] = get_csrf_token
    # event['get_params'] = get_params
    event['get_module_menus'] = get_module_menus
    event['get_module_submenus'] = get_module_submenus


# def get_params(request, params, alternate=None, settings=None):
#     return get_params(params, alternate, settings)


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
    _logging.debug(f"get_params: {params}, {alternate}")

    if not settings:
        settings = get_settings()
    result = settings and params in settings and \
        settings[params].strip() or None
    if not result:
        row = Parameter.query_kode(params).first()
        result = row and row.value or None

    return result and result or alternate


def _get_ini(request, var):
    return get_ini(var)


def get_ini(var):
    settings = get_settings()
    if var in settings and settings[var]:
        return settings[var]
    return


def get_password_strength(request):
    settings = get_settings()
    if 'password_strength' in settings and settings['password_strength']:
        return settings['password_strength']
    return True


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


def get_id_card_folder(ext=None, settings=None):
    _logging.debug('get_id_card_folder')
    idcard_files = get_params("partner_idcard_folder",
                              '/tmp/idcard', settings=settings)
    if ext:
        idcard_files += ext
        # if ext and os.sep != '/':
        #     ext = ext.replace('/', '\\')

    if os.sep != '/':
        idcard_files = idcard_files.replace('/', '\\')

    if not os.path.exists(idcard_files):
        os.makedirs(idcard_files)
    _logging.info(f"IDCard Files: {idcard_files}")
    return idcard_files


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
        return ids.split('\n')
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
    json_r.add_adapter(datetime.datetime, lambda v,
                       request: format_datetime(v))
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

def get_urls(url):
    home = get_params('_host', "")
    if home:
        urls = url.split(":")
        homes = home.split(":")
        if len(urls) > 1:
            if urls[0] != homes[0]:
                return ":".join([homes[0], ":".join(urls[1:])])
        else:
            return home + url
    return url


def get_host(request):
    host = get_params('_host', "")
    return host and host or get_home(request)


def get_home(request):
    return request.route_url('home')[:-1]


def _set_routes1(config, app_id):
    q = DBSession.query(Route).filter(Route.path != None,
                                      Route.module == None, Route.status == 1)
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


def _set_routes2(config, module="base"):
    q = DBSession.query(Route).filter(
        Route.module == module, Route.status == 1)
    for route in q:
        if route.type == 0:
            config.add_route(route.kode, route.path)
            if route.nama:
                titles[route.kode] = route.nama
        elif route.type == 1:
            config.add_jsonrpc_endpoint(
                route.kode, route.path, default_renderer="json_rpc")
    return q

def _add_view_config(config, view_name, route):
    if route.get("type") == 0:
        config.add_route(route.get("kode"), route.get("path"))
        if route.get("nama"):
            titles[route.get("kode")] = route.get("nama")
    elif route.get("type") == 1:
        config.add_jsonrpc_endpoint(route.get("kode"), route.get("path"),
                                        default_renderer="json_rpc")
    if not route.get("def_func"):
        return

    class_view = route.get("class_view") and f".{route.get('class_view')}" or ""
    class_name = f"{view_name}{class_view}"
    attr = f"view_{route.get("def_func")}"
    try:
        _views = importlib.import_module(class_name)
        views = _views
        if route.get("template") == "json":
            renderers = route.get("template")
        else:
            renderers = "views/templates/" + route.get("template")
        params = dict(attr=f"{attr}", route_name=route.get("kode"),
                        renderer=renderers)
        if route.get("permission"):
            params["permission"] = route.get("permission")
        config.add_view(views.Views, **params)
    except Exception as e:
            _logging.error(str(e))
            _logging.error(route)



def add_view_config(config, module, view_name):
    """
    Digunakan untuk mengenerate view_config berdasarkan tabel Routes
    config: config
    module: application module
    views: class or file tobe imported
    """
    q = DBSession.query(Route).filter(
        Route.module == module, Route.status == 1)
    for row in q.all():
        if row.type == 0:
            config.add_route(row.kode, row.path)
            if row.nama:
                titles[row.kode] = row.nama
        elif row.type == 1:
            config.add_jsonrpc_endpoint(row.kode, row.path,
                                        default_renderer="json_rpc")
        if not row.def_func:
            continue

        class_view = row.class_view and f".{row.class_view}" or ""
        class_name = f"{view_name}{class_view}"
        attr = f"view_{row.def_func}"
        try:
            _views = importlib.import_module(class_name)
            views = _views
            if row.template == "json":
                renderers = row.template
            else:
                renderers = "views/templates/" + row.template
            params = dict(attr=f"{attr}", route_name=row.kode,
                          renderer=renderers)
            if row.permission:
                params["permission"] = row.permission
            config.add_view(views.Views, **params)
        except Exception as e:
            _logging.error(str(e))
            _logging.error(dict(row.__dict__))

    config.scan('.')


def set_routes(config, app_id=None):
    if app_id and type(app_id) == str:
        return _set_routes2(config, app_id)
    else:
        return _set_routes1(config, app_id)


def get_route_names(rows):
    return [r.kode for r in rows if not r.is_menu]


def get_children(rows):
    # _logging.debug(f"Children: {dict(rows.__dict__)}")
    return [dict(
        order_id=r.order_id,
        id=r.id,
        path=r.path, nama=r.nama, is_menu=r.is_menu,
        icon=r.icon,
        permission=r.permission,
        route_names=[r.kode] + get_route_names(r.children),
        children=get_children(r.children),
        has_sub=r.path.find("/") == -1
    ) for r in rows if r.is_menu and r.status == 1]


def get_module_menus(module):
    query = DBSession.query(Route) \
        .filter(Route.module == module,
                Route.is_menu == 1,
                Route.parent_id == None)

    result = get_children(query.order_by(Route.order_id))
    # _logging.debug(result)
    return result


def get_module_submenus(parent_id):
    q = DBSession.query(Route) \
        .filter(Route.parent_id == parent_id) \
        .order_bY(Route.order_id)
    return [r.kode for r in q.all()]


partner_idcard_url = 'partner/idcard'


def get_config(settings):
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings,
                          root_factory='opensipkd.models.RootFactory',
                          session_factory=session_factory)
    config.set_default_csrf_options(require_csrf=False)
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
    config.add_request_method(get_host, 'home', reify=True)
    # config.add_request_method(get_captcha_url, 'captcha', reify=True)
    # config.add_request_method(get_urls, 'route_urls', reify=True)
    config.add_request_method(google_signin_client_id,
                              'google_signin_client_id', reify=True)
    config.add_request_method(google_signin_client_ids,
                              'google_signin_client_ids', reify=True)
    config.add_request_method(allow_register, 'allow_register', reify=True)
    config.add_request_method(disable_responsive, 'disable_responsive',
                              reify=True)
    config.add_request_method(_get_ini, 'get_ini', reify=True)
    config.add_request_method(_get_params, 'get_params', reify=True)
    config.add_request_method(get_csrf_token, 'get_csrf_token', reify=True)

    # Penambahan Module Auto Generate Menu
    # config.add_request_method(get_module_menus, 'get_module_menus', reify=True)
    # config.add_request_method(get_module_submenus, 'get_module_submenus', reify=True)

    # config.add_translation_dirs('opensipkd.base:locale/')

    partner_files = get_params("partner_files", settings=settings,
                               alternate="/tmp/partner")
    captcha_files = get_params('captcha_files', settings=settings,
                               alternate="/tmp/captcha")

    if os.sep != '/':
        captcha_files = captcha_files.replace('/', '\\')
        partner_files = partner_files.replace('/', '\\')

    _logging.info(f"Captcha Files: {captcha_files}")
    _logging.info(f"Partner Files: {partner_files}")
    if not os.path.exists(captcha_files):
        os.makedirs(captcha_files)
    if not os.path.exists(partner_files):
        os.makedirs(partner_files)

    config.add_static_view('static', 'opensipkd.base:static',
                           cache_max_age=3600)

    config.add_static_view('deform_static', 'deform:static')

    config.add_static_view(partner_idcard_url,
                           get_id_card_folder("/", settings=settings),
                           cache_max_age=3600)

    config.add_static_view('captcha', captcha_files)
    config.add_static_view('partner/files', partner_files)

    config.add_renderer('csv', 'opensipkd.tools.CSVRenderer')
    config.add_renderer('json', json_renderer())
    config.add_renderer('json_rpc', json_rpc())
    config.registry['mailer'] = mailer_factory_from_settings(settings)
    set_routes(config)
    routes_by_array(config)
    config.scan()
    _logging.debug(config)
    return config


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    default_resource_registry.registry['jquery.maskMoney'] = {
        None: {"js": "opensipkd.base:static/jquery/jquery.maskMoney.min.js"}}

    engine = engine_from_config(
        settings, 'sqlalchemy.', client_encoding='utf8',
        max_identifier_length=30)  # , convert_unicode=True
    DBSession.configure(bind=engine)
    LogDBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'

    locale.setlocale(locale.LC_ALL, settings['localization'])
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone

    # modules = get_modules(settings)
    # from importlib import import_module
    # for module in modules:
    #     # compatibility
    #     if module == 'admin':
    #         continue
    #     module = module.replace('/', '.')
    #     mfile = module
    #     m = import_module(mfile)
    #     cfg = m.main(config, **settings)
    #     if cfg:
    #         config = cfg

    return get_config(settings=settings).make_wsgi_app()


def routes_by_array(config, routs=routes):
    # New Routes By Array
    for route in routs:
        if len(route) > 4 and str(route[4]) == '1':
            config.add_jsonrpc_endpoint(
                route[0], route[1], default_renderer="json_rpc")
        else:
            config.add_route(route[0], route[1])
        titles[route[0]] = route[2]
