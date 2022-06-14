import locale
import logging
import re

# from opensipkd.base.tools.this_framework import api_has_permission_

try:
    from urllib import (urlencode, quote, quote_plus, )
except ImportError:
    from urllib.parse import (urlencode, quote, quote_plus, )

from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound,
)
from pyramid.renderers import JSON
from pyramid_mailer import mailer_factory_from_settings
import datetime, decimal
from sqlalchemy import engine_from_config, or_
from .security import (
    group_finder,
    get_user,
)
from .models import (
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
    dmy,
)

from deform import ZPTRendererFactory, Form
from pkg_resources import resource_filename

import os

from .models.handlers import LogDBSession

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
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path_req = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path_req.endswith('/'):
            noslash_path = path_req.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        return self.notfound_view(context, request)


# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, perm_names, context=None):
    if isinstance(perm_names, str):
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name, context):
            return True


@subscriber(BeforeRender)
def add_global(event):
    event['has_permission'] = has_permission_
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
    result = settings and params in settings and settings[params].strip() or None
    if not result:
        row = Parameter.query_kode(params).first()
        result = row and row.value or None

    return result and result or alternate


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


def get_ini(request, var):
    settings = get_settings()
    if var in settings and settings[var]:
        return settings[var]
    return


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
    modules = 'modules' in settings and settings['modules'] and settings['modules'].split(',') or []
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


def json_renderer():
    json_r = JSON()
    json_r.add_adapter(datetime.datetime, lambda v, request: dmy(v))
    json_r.add_adapter(datetime.date, lambda v, request: dmy(v))
    json_r.add_adapter(decimal.Decimal, lambda v, request: str(v))
    return json_r


def json_rpc():
    json_r = JSON()
    json_r.add_adapter(datetime.datetime, lambda v, request: v.isoformat())
    json_r.add_adapter(datetime.date, lambda v, request: v.isoformat())
    json_r.add_adapter(decimal.Decimal, lambda v, request: str(v))
    return json_r


class MyAuthenticationPolicy(AuthTktAuthenticationPolicy):
    def authenticated_userid(self, request):
        user = request.user
        if user is not None:
            return user.id


def get_host(request):
    host = get_params('_host', "")
    if not host:
        proto = 'HTTP_X_FORWARDED_PROTO' in request.environ \
                and request.environ['HTTP_X_FORWARDED_PROTO'] \
                or "http"
        host = f"{proto}://{request.host}"
    return host


def get_home(request):
    return request.route_url('home')


def set_routes(config, app_id=None):
    q = DBSession.query(Route)
    if not app_id:
        q.filter(or_(Route.app_id == 0, Route.app_id == None))
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
                          root_factory='opensipkd.base.models.RootFactory',
                          session_factory=session_factory)

    modules = get_modules(settings)
    # print(modules)
    from importlib import import_module
    for module in modules:
        if module == 'admin':
            continue
        module = module.replace('/', '.')
        mfile = module
        print(">>Load Module:", mfile)
        m = import_module(mfile)
        cfg = m.main(config, **settings)
        if cfg:
            config = cfg
        # todo apakah config bisa dikirim ke module?
        #     contoh:
        #        config = m.config(config)
    # dipindahkan ke config pyramid.include
    # config.include('pyramid_beaker')
    # config.include('pyramid_chameleon')

    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', callback=group_finder, hashalg='sha512')

    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    # config.set_security_policy(authz_policy)
    config.set_authorization_policy(authz_policy)

    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_request_method(get_company, 'company', reify=True)
    config.add_request_method(get_departement, 'departement', reify=True)
    config.add_request_method(get_ibukota, 'ibukota', reify=True)
    config.add_request_method(get_address, 'address', reify=True)
    config.add_request_method(get_address2, 'address2', reify=True)
    config.add_request_method(get_app_name, 'app_name', reify=True)
    config.add_request_method(get_modules, 'modules', reify=True)
    config.add_request_method(get_menus, 'menus', reify=True)
    config.add_request_method(thousand, 'thousand', reify=True)
    config.add_request_method(is_devel, 'devel', reify=True)
    config.add_request_method(get_host, '_host', reify=True)
    config.add_request_method(get_home, 'home', reify=True)
    # config.add_request_method(api_has_permission_, 'api_has_permission', reify=True)

    config.add_request_method(google_signin_client_id, 'google_signin_client_id', reify=True)
    config.add_request_method(google_signin_client_ids, 'google_signin_client_ids', reify=True)
    config.add_request_method(allow_register, 'allow_register', reify=True)
    config.add_request_method(disable_responsive, 'disable_responsive', reify=True)
    config.add_request_method(get_params, 'get_params', reify=True)

    # config.add_notfound_view(RemoveSlashNotFoundViewFactory())
    config.add_static_view('static', 'opensipkd.base:static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    # config.add_static_view('files', get_params('static_files'))
    # Captcha

    captcha_files = get_params('captcha_files', settings=settings,alternate="/tmp/captcha")
    if not os.path.exists(captcha_files):
        os.makedirs(captcha_files)
    config.add_static_view('captcha', captcha_files)
    # config.add_static_view('tts', path=get_params('tts_files'))

    config.add_renderer('csv', 'opensipkd.tools.CSVRenderer')
    config.add_renderer('json', json_renderer())
    # dipindahkan ke config pyramid.include
    # config.include('pyramid_rpc.jsonrpc')
    config.add_renderer('json_rpc', json_rpc())

    # q = DBSession.query(Route)
    # for route in q:
    #     if route.type == 0:
    #         config.add_route(route.kode, route.path)
    #         if route.nama:
    #             titles[route.kode] = route.nama
    #     elif route.type == 1:
    #         config.add_jsonrpc_endpoint(route.kode, route.path,
    #                                     default_renderer="json_rpc")
    set_routes(config)
    ###########################################
    # MAP
    # todo apabila config bosa di get dari module maka baris ini bisa hilang
    # Sudah solve menggunakan includeme
    ###########################################
    # if 'opensipkd.map.base' in modules:
    #     import papyrus
    #     from papyrus.renderers import GeoJSON, XSD
    #
    #     config.add_request_method(get_gmap_key, 'gmap_key', reify=True)
    #     config.add_request_method(get_bing_key, 'bing_key', reify=True)
    #     config.add_request_method(get_extent, 'extent', reify=True)
    #
    #     config.include(papyrus.includeme)
    #     config.add_renderer('geojson', GeoJSON())
    #     config.add_renderer('xsd', XSD())
    #     config.add_static_view('static_map', 'opensipkd.map.base:static', cache_max_age=3600)

    # if 'opensipkd.map.aset' in modules:
    #     config.add_static_view('static_map_aset', 'opensipkd.map.aset:static', cache_max_age=3600)
    #
    # # if 'opensipkd.map.pbb' in modules:
    # #     config.add_static_view('static_map_pbb', 'opensipkd.map.pbb:static', cache_max_age=3600)
    #
    # if 'opensipkd.pasar.web' in modules:
    #     config.add_static_view('static_pasar', 'opensipkd.pasar.web:static', cache_max_age=3600)
    #
    # if 'opensipkd.pbb.master' in modules:
    #     config.add_static_view('static_pbb', 'opensipkd.pbb.master:static', cache_max_age=3600)
    # if 'opensipkd.pos.pbb' in modules:
    #     config.add_static_view('static_pospbb', 'opensipkd.pos.pbb:static', cache_max_age=3600)

    config.registry['mailer'] = mailer_factory_from_settings(settings)
    # config.include()
    config.scan()
    for m in modules:
        config.scan(m)

    return config.make_wsgi_app()
