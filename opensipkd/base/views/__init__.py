import logging
from datetime import timedelta

import colander
from deform import (
    Form, ValidationFailure, widget, Button, )
from pyramid.httpexceptions import (
    HTTPFound, HTTPForbidden, HTTPNotFound, HTTPInternalServerError,
    HTTPSeeOther)
from pyramid.i18n import TranslationStringFactory
from pyramid.interfaces import IRoutesMapper
from pyramid.response import Response
from pyramid.view import view_config

from opensipkd.base import get_params
from .base_views import BaseView
from ..models import (
    DBSession, UserService, )
from .common import DataTables, ColumnDT

_ = TranslationStringFactory('login')
log = logging.getLogger(__name__)


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


@view_config(context=HTTPInternalServerError, renderer='templates/500.pt')
def internal_server_error(request):
    return {}
    # response = Response('Terjadi kesahala')
    # response.status_int = 500
    # return response


########
# Home #
########
class Home(BaseView):
    @view_config(route_name='home', renderer='templates/home.pt')
    def view_home(self):
        request = self.req
        # session = request.session
        modules = request.menus
        modules_default = get_params('modules_default')
        # request.session['modules'] = modules
        # request.session['modules_default'] = modules_default
        log.info(request.session.peek_flash())
        if modules_default:
            if request.user and request.has_permission(modules_default):
                return HTTPFound(location=request.route_url(modules_default))
            elif request.user and len(request.session.peek_flash('error')) < 2:
                return HTTPFound(location=request.route_url(modules_default))
            elif not request.user:
                return HTTPFound(location=request.route_url(modules_default))
        logo = get_params('logo', "static/img/logo.png")
        return dict(modules=modules, logo=logo)


@view_config(context=HTTPForbidden, renderer='templates/403.pt')
def http_forbidden(request):
    # if request.authenticated_userid:  # (request):
    #     request.session.flash('Hak Akses Terbatas', 'error')
    #     return HTTPFound(location=request.route_url('home'))
    # return HTTPFound(location=request.route_url('login'))

    if not request.is_authenticated:
        next_url = request.route_url('login', _query={'next': request.url})
        # next_url = f'{get_params("_host").strip()}/{next_url}'
        # log.info(next_url)
        return HTTPSeeOther(location=next_url)
    request.response.status = 403

    return {"url": request.url}


###################
# Change password #
###################
class Password(colander.Schema):
    old_password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())
    new_password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())
    retype_password = colander.SchemaNode(
        colander.String(), widget=widget.PasswordWidget())


def password_validator(form, value):
    if not UserService.check_password(form.request.user, value['old_password']):
        raise colander.Invalid(form, 'Invalid old password.')
    if value['new_password'] != value['retype_password']:
        raise colander.Invalid(form, 'Retype mismatch.')


@view_config(
    route_name='password', renderer='templates/chg_password.pt', permission='view')
def view_password(request):
    schema = Password(validator=password_validator)
    btn_save = Button('save', _('Simpan'))
    btn_cancel = Button('cancel', _('Batal'))
    buttons = (btn_save, btn_cancel)
    form = Form(schema, buttons=buttons)
    if not request.POST:
        return dict(form=form.render())
    if 'save' not in request.POST:
        return HTTPFound(location=request.route_url('home'))
    schema.request = request
    controls = request.POST.items()
    try:
        c = form.validate(controls)
    except ValidationFailure as e:
        return dict(form=e.render())
    UserService.set_password(request.user, c['new_password'])
    DBSession.add(request.user)
    request.session.flash('Password baru Anda sudah disimpan.')
    return HTTPFound(location=request.route_url('home'))


######################################
# Change password with security code #
######################################
one_hour = timedelta(1.0 / 24)
two_minutes = timedelta(1.0 / 24 / 60)


@colander.deferred
def deferred_jenis(node, kw):
    values = kw.get('daftar_jenis', [])
    return widget.RadioChoiceWidget(values=values)
