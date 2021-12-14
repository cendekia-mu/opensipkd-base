from datetime import datetime
import colander
from datatables import ColumnDT, DataTables
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
from opensipkd.tools.buttons import btn_close, btn_cancel, btn_save

from ..models import (
    DBSession,
    Parameter)

# from okeuangan.views.base_view import BaseViews


SESS_ADD_FAILED = 'Tambah parameter gagal'
SESS_EDIT_FAILED = 'Edit parameter gagal'


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        oid="kode",
        title="Kode")

    nama = colander.SchemaNode(
        colander.String(),
        oid="nama",
        title="Nama")

    value = colander.SchemaNode(
        colander.String(),
        widget=widget.TextAreaWidget(rows=5),
        oid="value",
        title="Nilai")

    status = colander.SchemaNode(
        colander.Boolean())


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))
    # id = colander.SchemaNode(
    # colander.Integer(),
    # oid="id",)


########
# List #
########
@view_config(route_name='parameter', renderer='templates/parameter/list.pt',
             permission='user-edit')
def view_list(request):
    return dict(a={})


##########
# Action #
##########
@view_config(route_name='parameter-act', renderer='json',
             permission='user-edit')
def parameter_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict

    if url_dict['act'] == 'grid':
        columns = [ColumnDT(Parameter.id, mData="id"),
                   ColumnDT(Parameter.kode, mData="kode"),
                   ColumnDT(Parameter.nama, mData="nama"),
                   ColumnDT(Parameter.value, mData="value"),
                   ColumnDT(Parameter.status, mData="status")]

        query = DBSession.query().select_from(Parameter)
        row_table = DataTables(req.GET, query, columns)
        return row_table.output_result()

    elif url_dict['act'] == 'hon':
        term = 'term' in params and params['term'] or ''
        rows = DBSession.query(Parameter.id, Parameter.nama
                               ).filter(
            Parameter.nama.ilike('%{term}%'.format(term=term))). \
            order_by(Parameter.nama).all()
        r = []
        for k in rows:
            d = dict(id=k[0],
                     value=k[1])
            r.append(d)
        return r


#######
# Add #
#######
def form_validator(form, value):
    pass


def get_form(request, class_form, row=None, buttons=(btn_save, btn_cancel)):
    schema = class_form(validator=form_validator)
    schema = schema.bind()  # perm_choice=PERM_CHOICE)
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=buttons)


def save(values, user, row=None):
    if not row:
        row = Parameter()
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
    request.session.flash('Parameter sudah disimpan.')


def routes_list(request):
    return HTTPFound(location=request.route_url('parameter'))


def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r


@view_config(route_name='parameter-add', renderer='templates/parameter/add.pt',
             permission='user-edit')
def view_add(request):
    req = request
    ses = req.session
    form = get_form(request, AddSchema)
    if req.POST:
        if 'simpan' in req.POST:
            controls = list(req.POST.items())
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                form.set_appstruct(e.cstruct)
                return dict(form=form)

            save_request(request, dict(controls))
        return routes_list(request)
    elif SESS_ADD_FAILED in req.session:
        return session_failed(request, SESS_ADD_FAILED)

    return dict(form=form)


########
# Edit #
########
def query_id(request):
    return DBSession.query(Parameter).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'Parameter ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return routes_list(request)


@view_config(route_name='parameter-edit', renderer='templates/parameter/edit.pt',
             permission='user-edit')
def view_edit(request):
    row = Parameter.query_id(request.matchdict['id']).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = list(request.POST.items())
            try:
                c = form.validate(controls)
            except ValidationFailure as e:
                form.set_appstruct(e.cstruct)
                return dict(form=form.render())

            save_request(request, dict(controls), row)
        return routes_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form.render())


@view_config(route_name='parameter-view', renderer='templates/parameter/edit.pt',
             permission='user-view')
def view_view(request):
    qry = query_id(request)
    row = qry.first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema, buttons=(btn_close,))
    if request.POST:
        return routes_list(request)

    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form.render(readonly=True))


##########
# Delete #
##########
@view_config(route_name='parameter-delete', renderer='templates/parameter/delete.pt',
             permission='user-edit')
def view_delete(request):
    q = Parameter.query_id(request.matchdict['id'])
    row = q.first()

    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus', 'batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Parameter ID %d %s sudah dihapus.' % (row.id, row.nama)
            try:
                q.delete()
                DBSession.flush()
            except:
                msg = 'Parameter ID %d %s tidak dapat dihapus.' % (row.id, row.nama)

            request.session.flash(msg)
        return routes_list(request)
    return dict(row=row,
                form=form.render())
