from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
)
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    Button,
)
from ..models import (
    DBSession,
    Route,
)
from datatables import (
    ColumnDT,
    DataTables,
)
from datetime import datetime
import json
ReadOnlyWidget = widget.TextInputWidget(readonly=True)

form_params = dict(scripts="")
list_params = dict(
    cols=[{'title': "ID", 'data': "id"},
          {'title': "Kode", 'data': "kode"},
          {'title': "Nama", 'data': "nama"},
          {'title': "Path", 'data': "path"},
          {'title': "Type", 'data': "typ",
           'class': "text-center", 'width': "50"},
          ],
    col_defs=json.dumps([
        {
            "searchable": False,
            "visible": False,
            "targets": [0],
        },
        {
            "searchable": True,
            "orderable": True,
            "targets": [1, 2, 3],
        }
    ]),
    buttons='btn_view, btn_add, btn_edit_no_id, btn_delete, btn_close',
    url="/routes"
)

class EditSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(), widget=widget.HiddenWidget())
    path = colander.SchemaNode(
        colander.String(), title='Path')
    nama = colander.SchemaNode(
        colander.String(), title='Nama')


def form_validator(form, values):
    def err_nama():
        raise colander.Invalid(
            form,
            'Nama %s sudah digunakan oleh ID %s' % (values['nama'], found.id)
        )

    def err_kode():
        raise colander.Invalid(
            form,
            'Kode %s sudah digunakan oleh ID %s' % (values['kode'], found.id)
        )

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Route).filter_by(id=uid)
        row = q.first()
    else:
        row = None

    # cek nama
    q = Route.query(). \
        filter_by(nama=values['nama'])
    found = q.first()
    if row:
        if found and found.id != row.id:
            err_nama()
    elif found:
        err_nama()

    # cek kode
    q = Route.query(). \
        filter_by(kode=values['kode'])
    found = q.first()
    if row:
        if found and found.id != row.id:
            err_kode()
    elif found:
        err_kode()


########
# List #
########   
@view_config(
    route_name='routes', renderer='templates/list.pt',
    permission='edit-title')
def view_list(request):
    return list_params


##########
# Action #
##########    
@view_config(
    route_name='routes-act', renderer='json', permission='edit-title')
def routes_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    if url_dict['act'] == 'grid':
        columns = []
        columns.append(ColumnDT(Route.id, mData="id"))
        columns.append(ColumnDT(Route.kode, mData="kode"))
        columns.append(ColumnDT(Route.nama, mData="nama"))
        columns.append(ColumnDT(Route.path, mData="path"))
        columns.append(ColumnDT(Route.type, mData="typ"))
        query = DBSession.query().select_from(Route)
        rowTable = DataTables(req.GET, query, columns)
        return rowTable.output_result()
    elif url_dict['act'] == 'hon':
        term = 'term' in params and params['term'] or ''
        rows = DBSession.query(Route.id, Route.nama
                               ).filter(
            Route.nama.ilike('%{term}%'.format(term=term))). \
            order_by(Route.nama).all()
        r = []
        for k in rows:
            d = dict(id=k[0], value=k[1])
            r.append(d)
        return r


def get_form(request, class_form, row=None):
    schema = class_form()  # validator=form_validator
    schema.request = request
    return Form(schema, buttons=('simpan', 'tutup'))


def save(values, user, row=None):
    if not row:
        row = Route()
        row.created = datetime.now()
        row.create_uid = user.id
    row.from_dict(values)
    row.updated = datetime.now()
    row.update_uid = user.id
    row.status = 'status' in values and values['status'] and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Routes sudah disimpan.')


def routes_list(request):
    return HTTPFound(location=request.route_url('routes'))


########
# Edit #
########
def query_id(request):
    return DBSession.query(Route).filter_by(id=request.matchdict['id'])


@view_config(
    route_name='routes-edit', renderer='templates/form-simple.pt',
    permission='edit-title')
def view_routes_edit(request):
    row = Route.query_id(request.matchdict['id']).first()
    if not row:
        return HTTPNotFound()
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = list(request.POST.items())
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                form.render(e.cstruct)
                return dict(form=form)

            save_request(request, dict(c), row)
        return routes_list(request)

    values = row.to_dict()
    return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)
