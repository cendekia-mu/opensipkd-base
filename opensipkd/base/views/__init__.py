import logging
from datetime import timedelta
import colander
from deform import (
    Form, ValidationFailure, widget, Button, FileData)
from pyramid.httpexceptions import (
    HTTPFound, HTTPForbidden, HTTPNotFound, HTTPInternalServerError,
    HTTPSeeOther)
from pyramid.i18n import TranslationStringFactory
from pyramid.interfaces import IRoutesMapper
from pyramid.renderers import render_to_response
from pyramid.view import view_config

from opensipkd.base import get_params, get_urls
from opensipkd.models import (
    DBSession, UserService, )
from opensipkd.tools import mem_tmp_store
from .base_views import BaseView, DataTables

_ = TranslationStringFactory('login')
log = logging.getLogger(__name__)
from datatables import ColumnDT
# , DataTables, get_urls)

def no_action():
    test = ColumnDT

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


# @view_config(context=HTTPNotFound, renderer='json')
# def not_found_json(request):
#     pass
    # request.response.status = 404
    # return {"JSON"}


@view_config(context=HTTPInternalServerError, renderer='templates/500.pt')
def internal_server_error(request):
    return {}
    # response = Response('Terjadi kesahala')
    # response.status_int = 500
    # return response


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
        submodules_default = get_params('submenus')
        # request.session['modules'] = modules
        # request.session['modules_default'] = modules_default
        log.info(request.session.peek_flash())
        if modules_default:
            if request.user and request.has_permission(modules_default):
                return HTTPFound(location=get_urls(request.route_url(modules_default)))
            elif request.user and len(request.session.peek_flash('error')) < 2:
                return HTTPFound(location=get_urls(request.route_url(modules_default)))
            elif not request.user:
                return HTTPFound(location=get_urls(request.route_url(modules_default)))
        logo = get_params('logo', "static/img/logo.png")
        home_tpl = get_params("home_tpl")
        if home_tpl:
            return render_to_response(
                home_tpl,
                dict(modules=modules, logo=logo, submodules=[]),
                request=request
            )
        return dict(modules=modules, logo=logo, submodules=[])


@view_config(context=HTTPForbidden, renderer='templates/403.pt')
def http_forbidden(request):
    if not request.is_authenticated:
        next_url = get_urls(request.route_url('login', _query={'next': request.url}))
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
        colander.String(), widget=widget.CheckedPasswordWidget())
    # retype_password = colander.SchemaNode(
    # colander.String(), widget=widget.PasswordWidget())


def password_validator(form, value):
    if not UserService.check_password(form.request.user, value['old_password']):
        raise colander.Invalid(form, 'Invalid old password.')
    # if value['new_password'] != value['retype_password']:
    # raise colander.Invalid(form, 'Retype mismatch.')


@view_config(
    route_name='password', renderer='templates/chg_password.pt',
    permission='view')
def view_password(request):
    schema = Password(validator=password_validator)
    btn_save = Button('save', _('Simpan'))
    btn_cancel = Button('cancel', _('Batal'))
    buttons = (btn_save, btn_cancel)
    form = Form(schema, buttons=buttons)
    if not request.POST:
        return dict(form=form.render())
    if 'save' not in request.POST:
        return HTTPFound(location=request._host)
    schema.request = request
    controls = request.POST.items()
    try:
        c = form.validate(controls)
    except ValidationFailure as e:
        return dict(form=e.render())
    UserService.set_password(request.user, c['new_password'])
    DBSession.add(request.user)
    request.session.flash('Password baru Anda sudah disimpan.')
    return HTTPFound(location=request._host)


######################################
# Change password with security code #
######################################
one_hour = timedelta(1.0 / 24)
two_minutes = timedelta(1.0 / 24 / 60)


@colander.deferred
def deferred_jenis(node, kw):
    values = kw.get('daftar_jenis', [])
    return widget.RadioChoiceWidget(values=values)