import locale
import logging
import os
import importlib
import csv
import re
import datetime
import decimal
from pyramid.renderers import JSON
from pyramid_beaker import session_factory_from_settings
from pyramid.config import Configurator
from pyramid.events import NewRequest, BeforeRender, subscriber
from pyramid_mailer import mailer_factory_from_settings

from opensipkd.tools import get_settings, DefaultTimeZone, dmy, dmyhms
from .security import MySecurityPolicy, get_user
from sqlalchemy import engine_from_config
from  .models.base import DBSession
from .models.handlers import LogDBSession
from .models.meta import Base
from .models.users import init_model

from pkg_resources import resource_filename
# from deform import ZPTRendererFactory, Form
# from deform.widget import default_resource_registry

import deform
_logging = logging.getLogger(__name__)

# version 2.0.0 digunakan untuk change default template
deform_templates = resource_filename('deform', 'templates')
path = os.path.dirname(__file__)
path = os.path.join(path, 'widgets', 'templates')
search_path = (path, deform_templates)  # ,
renderer = deform.ZPTRendererFactory(search_path)
deform.Form.set_zpt_renderer(search_path)


main_title = 'openSIPKD'
titles = {}
static_route = []

titles = {}



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
    result = None
    if not settings:
        settings = get_settings()
    if settings:
        result = settings.get(params)
    _logging.debug(
        f"get_params: {params}, Alternate: {alternate} Settings: {not settings == None} Result: {result}")
    return result and result.strip() or alternate

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

        _logging.debug(f"Headers: {headers}")
        response.headers.update(headers)

    event.request.add_response_callback(cors_headers)

def get_app_name(request):
    return get_params('app_name', 'openSIPKD Application')

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
    # if not menus:
    #     return get_modules(get_settings())

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

def get_home(request):
    return request.route_url('base-home')[:-1]

def get_host(request):
    host = get_params('_host', "")
    return host and host or get_home(request)

def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]

def get_company(request):
    return get_params('company', 'openSIPKD').upper()

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

def allow_register(request):
    return BASE_CLASS.allow_register

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


def get_config(settings):
    session_factory = session_factory_from_settings(settings)
    config = Configurator(settings=settings,
                          root_factory='opensipkd.base.models.users.RootFactory',
                          session_factory=session_factory)
    config.set_default_csrf_options(require_csrf=False)
    config.set_security_policy(MySecurityPolicy(settings["session.secret"]))
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    config.add_request_method(get_app_name, 'app_name', reify=True)
    config.add_request_method(get_menus, 'menus', reify=True)
    # config.add_request_method(get_host, '_host', reify=True)
    config.add_request_method(get_host, 'home', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_request_method(get_company, 'company', reify=True)

    config.add_request_method(get_user, 'user', reify=True)
    #     config.add_request_method(get_departement, 'departement', reify=True)
    #     config.add_request_method(get_ibukota, 'ibukota', reify=True)
    #     config.add_request_method(get_address, 'address', reify=True)
    #     config.add_request_method(get_address2, 'address2', reify=True)

    #     config.add_request_method(get_modules, 'modules', reify=True)
    #     config.add_request_method(has_modules_, 'has_modules', reify=True)
    #     config.add_request_method(thousand, 'thousand', reify=True)
    #     config.add_request_method(is_devel, 'devel', reify=True)
    config.add_request_method(google_signin_client_id,
                                'google_signin_client_id', reify=True)
    config.add_request_method(google_signin_client_ids,
                                  'google_signin_client_ids', reify=True)
    config.add_request_method(allow_register, 'allow_register', reify=True)
    #     config.add_request_method(disable_responsive, 'disable_responsive',
    #                               reify=True)
    #     config.add_request_method(_get_ini, 'get_ini', reify=True)
    # config.add_request_method(get_params, 'get_params', reify=True)
    #     config.add_request_method(get_csrf_token, 'get_csrf_token', reify=True)

    #     # Penambahan Module Auto Generate Menu
    #     # config.add_request_method(get_module_menus, 'get_module_menus', reify=True)
    #     # config.add_request_method(get_module_submenus, 'get_module_submenus', reify=True)

    #     # config.add_translation_dirs('opensipkd.base:locale/')

    #     partner_files = get_params("partner_files", settings=settings,
    #                                alternate="/tmp/partner")
    #     captcha_files = get_params('captcha_files', settings=settings,
    #                                alternate="/tmp/captcha")

    #     if os.sep != '/':
    #         captcha_files = captcha_files.replace('/', '\\')
    #         partner_files = partner_files.replace('/', '\\')

    #     _logging.info(f"Captcha Files: {captcha_files}")
    #     _logging.info(f"Partner Files: {partner_files}")
    #     if not os.path.exists(captcha_files):
    #         os.makedirs(captcha_files)
    #     if not os.path.exists(partner_files):
    #         os.makedirs(partner_files)

    config.add_static_view('static', 'opensipkd.base:static',
                            cache_max_age=3600)

    config.add_static_view('deform_static', 'deform:static')

    #     config.add_static_view(partner_idcard_url,
    #                            get_id_card_folder("/", settings=settings),
    #                            cache_max_age=3600)

    #     config.add_static_view('captcha', captcha_files)
    #     config.add_static_view('partner/files', partner_files)

    config.add_renderer('csv', 'opensipkd.tools.CSVRenderer')
    config.add_renderer('json', json_renderer())
    config.add_renderer('json_rpc', json_rpc())
    config.registry['mailer'] = mailer_factory_from_settings(settings)

    return config

def init_db(settings):
    engine = engine_from_config(
    settings, 'sqlalchemy.', client_encoding='utf8',
    max_identifier_length=30)  # , convert_unicode=True
    DBSession.configure(bind=engine)
    LogDBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # default_resource_registry.registry['jquery.maskMoney'] = {
    #     None: {"js": "opensipkd.base:static/jquery/jquery.maskMoney.min.js"}}
    if not settings.get('localization', ''):
        settings['localization'] = 'id_ID.UTF-8'

    locale.setlocale(locale.LC_ALL, settings['localization'])
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone
    # settings["captcha_files"] = "c:\\tmp\\captcha\\"
    tmp = get_params("temp_files", "/tmp", settings=settings)
    settings["captcha_files"] = os.path.join(tmp , "captcha") + os.sep

    init_db(settings=settings)
    config = get_config(settings=settings)

    BASE_CLASS.route_from_csv(config)
    BASE_CLASS.route_from_list(config)
    BASE_CLASS.static_view(config, settings=settings)
    config.scan()
    # _logging.debug(config)
    return config.make_wsgi_app()


def _add_route(config, route):
    if int(route.get("typ", 0)) == 0:
        config.add_route(route.get("kode"), route.get("path"))
    elif int(route.get("typ")) == 1:
        config.add_jsonrpc_endpoint(route.get("kode"), route.get("path"),
                                    default_renderer="json_rpc")
    if route.get("nama"):
        titles[route.get("kode")] = route.get("nama")


def _add_view_config(config, paket, route):
    _add_route(config, route)
    if not route.get("func_name"):
        func_name = "".join(route.get("kode").split('-')[-1:])
        route["func_name"] = "_".join(["view", func_name])

    file_name = f"{paket}.{route.get('file_name')}"
    # _logging.debug(f"File Name: {file_name}")
    attr = f"{route.get('func_name')}"
    try:
        _views = importlib.import_module(file_name)
        class_name = route.get("class_name", None)
        if not class_name:
            class_name = "Views"

        views = getattr(_views, class_name)
        template = route.get("template", "form.pt")
        if not template:
            if route.get("func_name") == "view_list":
                template = "list.pt"
            elif route.get("func_name") == "view_act":
                template = "json"
            else:
                template = "form.pt"

        if template != "json":
            template = "views/templates/" + template

        params = dict(attr=f"{attr}",
                      route_name=route.get("kode"),
                      renderer=template)
        if route.get("permission"):
            params["permission"] = route.get("permission")
        if route.get("crsf"):
            params["require_csrf"] = True

        config.add_view(views, **params)

    except Exception as e:
        _logging.error("Add View Config :{code} Kode {error}"\
                       .format(code=route["kode"], error=str(e)))
    _logging.debug(f"Route: {route.get('kode')} {route.get('path')}")




class BaseApp():
    def __init__(self):
        self.menus = []
        self.partner_doc = ""
        self.temp_files = ""
        self.allow_register = 0
        self.reg_form = ""
        self.reg_id_card = 0
        self.reg_captcha = 0
        self.captcha_files = ""
        self.login_captcha = 0
        self.base_dir = os.path.split(__file__)[0]

    def get_route_file(self, filename="routes.csv"):
        fullpath = os.path.join(self.base_dir, 'scripts', 'data', filename)
        return open(fullpath)

    def static_view(self, config, settings=None):
        self.partner_doc = get_params(
            "partner_doc", '/tmp/docs/partner', settings=settings)+os.sep
        if not os.path.exists(self.partner_doc):
            os.makedirs(self.partner_doc)
        config.add_static_view(
            'docs/partner', self.partner_doc, cache_max_age=0)
        self.temp_files = get_params(
            "temp_files", '/tmp', settings=settings)
        if not os.path.exists(self.temp_files):
            os.makedirs(self.temp_files)
        
        # Registrasi
        self.allow_register = get_params(
            "allow_register", 0, settings=settings)
        self.reg_form = get_params("reg_form", 'base-register')
        self.reg_id_card = get_params(
            "reg_id_card", 0, settings=settings)
        self.reg_captcha = get_params(
            "reg_captcha", 0, settings=settings)
        self.captcha_files = os.path.join(self.temp_files, "captcha")+os.sep

        if not os.path.exists(self.captcha_files):
            os.makedirs(self.captcha_files)
        config.add_static_view(
            'captcha', self.captcha_files, cache_max_age=0)

        self.login_tpl = get_params("login_tpl", "", settings=settings)
        self.login_captcha = int(get_params("login_captcha", 0, settings=settings))
        

    def add_menu(self, config, route_menus, parent=None, paket="opensipkd.base.views"):
        route_names = []
        for route in route_menus:
            # if not int(route.get("status", 0)):
            # continue

            route["route_name"] = [route["kode"]]
            route["permission"] = route.get("permission", "")
            route["icon"] = route.get("icon", None)
            route_typ = route.get("typ", 0)
            if route_typ == "" or route_typ == None:
                route_typ = 0
            else:
                route_typ = int(route_typ)

            route["typ"] = route_typ
            is_menu = route.get("is_menu", 0)
            route["is_menu"] = is_menu and int(is_menu) or 0

            url_path = route.get("path", None)
            if not url_path:
                path_split = route.get("kode").split("-")
                path_last = path_split[len(path_split) - 1]
                if path_last in ["edit", "view", "delete"]:
                    path = "/".join(path_split[:-1])
                    path += "/{id}/"+path_last
                elif path_last in ["act"]:
                    path = "/".join(path_split[:-1])
                    path += "/{act}/"+path_last
                else:
                    path = "/".join(path_split)
                url_path = '/'+path

            route["path"] = url_path

            children = route.get("children", [])
            route["children"] = []
            if route.get("file_name"):
                _add_view_config(config, paket, route)
            elif route["path"] != "#":
                _add_route(config, route)

            if route.get("is_menu", None):
                if not parent:
                    self.menus.append(route)
                else:
                    parent["children"].append(route)
            if children:
                route["route_name"].extend(
                    self.add_menu(config, children, route, paket)
                )
            route_names.append(route["kode"])
        return route_names

    def route_children(self, parent, row):
        for p in parent:
            parent_id = row.get("parent_id") or row.get(
                "parent_id/routes.kode")
            if p["kode"] == parent_id:
                p["children"].append(row)
            else:
                if p["children"]:
                    self.route_children(p["children"], row)

    def route_from_csv(self, config, paket="opensipkd.base.views", filename="routes.csv"):
        with self.get_route_file(filename) as f:
            rows = csv.DictReader(f)
            new_routes = []
            for row in rows:
                status = row.get("status", 0)
                if not row["kode"] or not int(status):
                    continue

                status = int(status)
                row["children"] = []
                parent_id = row.get("parent_id") or row.get("parent_id/routes.kode")
                if parent_id:
                    self.route_children(new_routes, row)
                else:
                    new_routes.append(row)

            self.add_menu(config, new_routes, None, paket)

    def route_from_list(self, config, routs=[], paket="opensipkd.base.views"):
        new_routes = []
        for route in routs:
            d = {"kode": route[0],
                 "path": route[1],
                 "nama": route[2],
                 "typ": len(route) > 4 and route[4] or 0
                 }
            new_routes.append(d)

        self.add_menu(config, new_routes, paket)

    def get_menus(self):
        _logging.debug(f"Menus: {self.menus}")
        return self.menus


BASE_CLASS = BaseApp()
# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c


def has_permission_(request, perm_names, context=None):
    if not perm_names:
        return False
    if isinstance(perm_names, str):
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name, context):
            return True


@subscriber(BeforeRender)
def add_global(event):
    event['has_permission'] = has_permission_
    event['get_base_menus'] = BASE_CLASS.get_menus
    
#     event['has_modules'] = has_modules_
#     event['urlencode'] = urlencode
#     event['quote_plus'] = quote_plus
#     event['quote'] = quote
#     event['money'] = money
#     event['should_int'] = should_int
#     event['thousand'] = thousand
#     event['as_timezone'] = as_timezone
#     event['split'] = split
#     event['allow_register'] = allow_register
#     event['change_unit'] = change_unit
    event['get_params'] = get_params_
#     event['get_urls'] = get_urls
#     event['get_csrf_token'] = get_csrf_token
#     event['get_base_menus'] = BASE_CLASS.get_menus

#     # event['get_params'] = get_params
#     # event['get_module_menus'] = get_module_menus
#     # event['get_module_submenus'] = get_module_submenus

def get_params_(params, alternate=None, settings=None):
    return get_params(params, alternate, settings)

# def get_urls(url):
#     home = get_params('_host', "")
#     if home:
#         urls = url.split(":")
#         homes = home.split(":")
#         if len(urls) > 1:
#             if urls[0] != homes[0]:
#                 return ":".join([homes[0], ":".join(urls[1:])])
#         else:
#             return home + url
#     return url
