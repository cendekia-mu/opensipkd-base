from pyramid.view import (
    view_config,
)
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
)
from pyramid.httpexceptions import (
    HTTPFound,
)
from pyramid.view import (
    view_config,
)

from opensipkd.models import Departemen
from ..views import BaseView

SESS_ADD_FAILED = 'Tambah departemen gagal'
SESS_EDIT_FAILED = 'Edit departemen gagal'


class AddSchema(colander.Schema):
    cur_departemen_nm = colander.SchemaNode(
        colander.String(),
        widget=widget.TextInputWidget(readonly=True),
        title="Departemen Kini",
        missing=colander.drop)
    departemen_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(),
        oid="departemen_id", )
    departemen_nm = colander.SchemaNode(
        colander.String(),
        # missing = colander.drop,
        oid="departemen_nm",
        title="Pilih Departemen")
    departemen_kd = colander.SchemaNode(
        colander.String(),
        # widget = widget.HiddenWidget(),
        oid="departemen_kd",
        title="Kode")
    level_id = colander.SchemaNode(
        colander.String(),
        # widget = widget.HiddenWidget(),
        oid="level_id",
        title="Level")
    callback = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        widget=widget.HiddenWidget(),
    )


class ChangeDepartemen(BaseView):
    ########
    # List #
    ########
    @view_config(route_name='departemen-chg', renderer='templates/departemen/chg.pt')
    def view_departemen_chg(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        form = get_form(request, AddSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    return dict(form=form)
                values = dict(controls)
                save_request(request, values)
                if 'callback' in values and values['callback']:
                    return HTTPFound(values['callback'])

            return route_list(request)

        referer = 'REFERER' in request.headers and request.headers['REFERER'] or ''
        values = dict(cur_departemen_nm=ses["departemen_nm"],
                      callback=referer)
        form.render(appstruct=values)
        return dict(form=form)


#######
# Add #
#######
def form_validator(form, value):
    def err_departemen():
        raise colander.Invalid(form,
                               'Departemen Tidak Ditemukan')

    q = Departemen.query_id(value['departemen_id'])
    found = q.first()
    if not found:
        err_departemen()


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def save_request(request, values, row=None):
    request.session['departemen_id'] = values['departemen_id']
    row = Departemen.query_id(values['departemen_id']).first()
    request.session['departemen_nm'] = row.nama
    request.session['departemen_kd'] = row.kode
    request.session.flash(
        'Departemen %s %s sudah diubah.' % (request.session['departemen_kd'], request.session['departemen_nm']))


def route_list(request):
    return HTTPFound(location=request.route_urls('home'))
