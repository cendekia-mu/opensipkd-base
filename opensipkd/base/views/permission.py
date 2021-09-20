# from ..tools import row2dict, xls_reader
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

from ..models import DBSession
from ..models import Permission
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah permission gagal'
SESS_EDIT_FAILED = 'Edit permission gagal'


class AddSchema(colander.Schema):
    perm_name = colander.SchemaNode(
        colander.String(),
        oid="perm_name",
        title="Nama")
    description = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        oid="description",
        title="Diskripsi")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ViewPermission(BaseView):
    ########
    # List #
    ########
    @view_config(route_name='permission', renderer='templates/permission/list.pt',
                 permission='user-edit')
    def view_list(self):
        return dict(a={})

    ##########
    # Action #
    ##########
    @view_config(route_name='permission-act', renderer='json',
                 permission='user-edit')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict

        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(Permission.id, mData='id'),
                ColumnDT(Permission.perm_name, mData='perm_name'),
                ColumnDT(Permission.description, mData='description'),
            ]
            query = DBSession.query().select_from(Permission)
            rowTable = DataTables(request.GET, query, columns)
            return rowTable.output_result()


    #######
    # ADD #
    #######

    @view_config(route_name='permission-add', renderer='templates/permission/add.pt',
                 permission='user-edit')
    def view_add(self):
        request = self.req
        form = get_form(request, AddSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form)
                save_request(request, dict(c))
            return route_list(request)

        return dict(form=form)

    ##########
    # Edit #
    ##########
    @view_config(route_name='permission-edit', renderer='templates/permission/edt.pt',
                 permission='user-edit')
    def view_edt(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)
        uid = row.id

        form = get_form(request, EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form)

                save_request(request, dict(controls), row)
            return route_list(request)

        val = row.to_dict()
        values = {}
        for v in val:
            if val[v]:
                values[v] = val[v]
        form.render(appstruct=values)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='permission-delete', renderer='templates/permission/del.pt',
                 permission='user-edit')
    def view_del(self):
        request = self.req
        q = query_id(request)
        row = q.first()

        if not row:
            return id_not_found(request)

        form = Form(colander.Schema(), buttons=('hapus', 'batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'permission ID %d sudah dihapus.' % (row.id)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return route_list(request)
        return dict(row=row, form=form.render())


#######    
# Add #
#######
def form_validator(form, value):
    # def err_kode():
    #     raise colander.Invalid(form,
    #         'Kode %s sudah digunakan oleh %s' % (
    #             value['kode'], found.nama))

    # def err_login():
    # raise colander.Invalid(form,
    # 'Login %s sudah digunakan oleh kode %s' % (
    # value['user_nm'], found.row.nama))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Permission).filter_by(id=uid)
        row = q.first()
    else:
        row = None

    # q = Permission.query_kode(value['kode']) #DBSession.query(Permission).filter_by(kode=value['kode'])
    # found = q.first()
    # if row:
    #     if found and found.id != row.id:
    #         err_kode()
    # elif found:
    #     err_kode()


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def save(values, user, row=None):
    if not row:
        row = Permission()

    values['perm_name'] = (values['perm_name'])
    values['description'] = (values['description'])
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Permission sudah disimpan.')
    return row


def route_list(request):
    return HTTPFound(location=request.route_url('permission'))


########
# Edit #
########
def query_id(request):
    return DBSession.query(Permission).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'Permission ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
