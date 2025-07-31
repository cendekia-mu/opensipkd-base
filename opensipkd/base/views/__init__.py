import logging

from translationstring import TranslationStringFactory
import colander
from pyramid.httpexceptions import (
    HTTPFound, HTTPForbidden, HTTPNotFound, HTTPInternalServerError,
    HTTPSeeOther)
from pyramid.interfaces import IRoutesMapper
from pyramid.view import view_config
from opensipkd.base import get_params, get_home
from pyramid.renderers import render_to_response
#, get_urls
from .base_views import BaseView
#, DataTables
from datetime import timedelta
from opensipkd.detable import *
from .common import ColumnDT, DataTables
from opensipkd.tools import mem_tmp_store
from deform import (
    Form, ValidationFailure, widget, Button, FileData)
_ = TranslationStringFactory('user')

one_hour = timedelta(1.0 / 24)
two_minutes = timedelta(1.0 / 24 / 60)

@view_config(context=HTTPNotFound, renderer='templates/404.pt')
def not_found(request):
    path = request.path
    registry = request.registry
    mapper = registry.queryUtility(IRoutesMapper)
    if mapper is not None and path.endswith('/'):
        noslash_path = path.rstrip('/')
        for route in mapper.get_routes():
            if route.match(noslash_path) is not None:
                qs = request.query_string
                if qs:
                    noslash_path += '?' + qs
                return HTTPFound(location=noslash_path)

    request.response.status = 404
    return {}

log = logging.getLogger(__name__)

@view_config(context=HTTPInternalServerError, renderer='templates/500.pt')
def internal_server_error(request):
    return {}



@view_config(context=HTTPForbidden, renderer='templates/403.pt')
def http_forbidden(request):
    if not request.is_authenticated:
        # next_url = get_urls(
        #     request.route_url(
        #     'login', _query={'next': request.url}))
        next_url = request.route_url('base-login', _query={'next': request.url})
        return HTTPSeeOther(location=next_url)

    request.response.status = 403
    return {"url": request.url}


class Validator(object):
    def __init__(self, row):
        self.row = row


class FileSchema(colander.Schema):
    file_name = colander.SchemaNode(
        FileData(),
        widget=widget.FileUploadWidget(mem_tmp_store, size=104857600),
        missing=colander.drop,
        title="File"
    )
    description = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=256),
    )


class FilesSchema(colander.SequenceSchema):
    file_name = FileSchema()

    def after_bin(self, node, kw):
        self["file_name"].title = ""

class Home(BaseView):
    # @view_config(route_name='home', renderer='templates/home.pt')
    def view_home(self):
        request = self.req
        # session = request.session
        modules = request.menus
        modules_default = get_params('modules_default')
        submodules_default = get_params('submenus')
        # request.session['modules'] = modules
        # request.session['modules_default'] = modules_default
        log.info(request.session.peek_flash())
        if modules_default:
            if request.user and request.has_permission(modules_default):
                return HTTPFound(location=request.route_url(modules_default))
                # return HTTPFound(location=get_urls(request.route_url(modules_default)))
            elif request.user and len(request.session.peek_flash('error')) < 2:
                return HTTPFound(location=request.route_url(modules_default))
                # return HTTPFound(location=get_urls(request.route_url(modules_default)))
            elif not request.user:
                return HTTPFound(location=request.route_url(modules_default))
                # return HTTPFound(location=get_urls(request.route_url(modules_default)))
                
        logo = get_params('logo', "static/img/logo.png")
        home_tpl = get_params("home_tpl")
        if home_tpl:
            return render_to_response(
                home_tpl,
                dict(modules=modules, logo=logo, submodules=[]),
                request=request
            )
        return dict(modules=modules, logo=logo, submodules=[])
