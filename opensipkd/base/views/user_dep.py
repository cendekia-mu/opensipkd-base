from datetime import datetime

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
from sqlalchemy.orm import aliased

from ..models import DBSession
from ..models import DepartemenUser, User, Departemen
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah departemen gagal'
SESS_EDIT_FAILED = 'Edit departemen gagal'


class AddSchema(colander.Schema):
    departemen_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(),
        oid="departemen_id",
        title="Departemen")

    departemen_nm = colander.SchemaNode(
        colander.String(),
        oid="departemen_nm",
        title="Departemen")

    user_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(),
        oid="user_id",
        title="User")

    user_nm = colander.SchemaNode(
        colander.String(),
        oid="user_nm",
        title="User")

    sub_departemen = colander.SchemaNode(
        colander.Boolean(),
        widget=widget.CheckboxWidget(),
        oid="sub_departemen",
        title="Allow Sub")


class EditSchema(AddSchema):
    id = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        widget=widget.HiddenWidget(readonly=True))


class ViewDepartemenUser(BaseView):
    ########
    # List #
    ########
    @view_config(route_name='departemen-user', renderer='templates/departemen_user/list.pt',
                 permission='departemen')
    def view_list(self):
        return dict(a={})

    ##########
    # Action #
    ##########
    @view_config(route_name='departemen-user-act', renderer='json',
                 permission='departemen')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        dep_alias = aliased(DepartemenUser)
        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(DepartemenUser.id, mData='id'),
                ColumnDT(User.user_name, mData='user_name'),
                ColumnDT(Departemen.nama, mData='dept_name'),
                ColumnDT(DepartemenUser.sub_departemen, mData='allow_sub'),
            ]
            query = DBSession.query().select_from(DepartemenUser) \
                .join(User, User.id == DepartemenUser.user_id) \
                .join(Departemen, DepartemenUser.departemen_id == Departemen.id)

            rowTable = DataTables(request.GET, query, columns)
            return rowTable.output_result()

    @view_config(route_name='departemen-user-add', renderer='templates/departemen_user/add.pt',
                 permission='departemen')
    def view_departemen_add(self):
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
                    return dict(form=e.render())
                save_request(request, dict(controls))
            return route_list(request)
        return dict(form=form.render())

    ########
    # Edit #
    ########
    @view_config(route_name='departemen-user-edt', renderer='templates/departemen_user/add.pt',
                 permission='departemen')
    def view_departemen_edt(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        row = query_id(request).first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    return dict(form=e.render())

                save_request(request, dict(controls), row)
            return route_list(request)

        values = row.to_dict()
        values['departemen_nm'] = row.departemen.nama + ';' + row.departemen.kode
        values['user_nm'] = row.user.user_name + '(' + row.user.email + ')'
        form = form.render(appstruct=values)
        return dict(form=form)

    ##########
    # Delete #
    ##########
    @view_config(route_name='departemen-user-del',
                 renderer='templates/departemen_user/del.pt',
                 permission='departemen')
    def view_delete(self):
        request = self.req
        q = query_id(request)
        row = q.first()

        if not row:
            return id_not_found(request)
        form = Form(colander.Schema(), buttons=('hapus', 'batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Departemen User ID %d departemen %s sudah dihapus.' % (row.id, row.departemen.nama)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return route_list(request)
        return dict(row=row, form=form.render())


#######
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
                               'Kode %s sudah digunakan oleh %s' % (
                                   value['kode'], found.nama))

    def err_nama():
        raise colander.Invalid(form,
                               'Uraian %s sudah digunakan oleh kode %s' % (
                                   value['nama'], found.kode))

    # if 'id' in form.request.matchdict:
    #     uid = form.request.matchdict['id']
    #     q = DBSession.query(DepartemenUser).filter_by(id=uid)
    #     urusan = q.first()
    # else:
    #     urusan = None
    #
    # q = DepartemenUser.query_kode(value['kode'])  # DBSession.query().filter_by(kode=value['kode'])
    # found = q.first()
    # if urusan:
    #     if found and found.id != urusan.id:
    #         err_kode()
    # elif found:
    #     err_kode()
    #
    # found = DepartemenUser.query_nama(value['nama']).first()
    # if urusan:
    #     if found and found.id != urusan.id:
    #         err_nama()
    # elif found:
    #     err_nama()


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def update_children(children):
    for child in children:
        child.level_id = child.parent.level_id + 1
        DBSession.add(child)
        DBSession.flush()
        if child.children:
            update_children(child.children)


def save(values, user, row=None):
    if not row:
        row = DepartemenUser()
        row.created = datetime.now()
        row.create_uid = user.id
    else:
        row.updated = datetime.now()
        row.update_uid = user.id

    row.from_dict(values)
    row.sub_departemen = 'sub_departemen' in values and values['sub_departemen'] and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash("Departemen User {nama} sudah disimpan.".format(nama=row.departemen.nama))


def route_list(request):
    return HTTPFound(location=request.route_url('departemen-user'))


def query_id(request):
    return DBSession.query(DepartemenUser).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'DepartemenUser ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
