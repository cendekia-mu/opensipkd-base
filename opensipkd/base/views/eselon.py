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

from ..models import (
    DBSession,
    Eselon
)
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah eselon gagal'
SESS_EDIT_FAILED = 'Edit eselon gagal'


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode")
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    status = colander.SchemaNode(
        colander.Boolean(),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class Views(BaseView):
    @view_config(route_name='eselon', renderer='templates/eselon/list.pt',
                 permission='eselon')
    def view_list(self):
        return dict(a={})

    ##########
    # Action #
    ##########
    @view_config(route_name='eselon-act', renderer='json',
                 permission='read')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict

        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(Eselon.id, mData='id'),
                ColumnDT(Eselon.kode, mData='kode'),
                ColumnDT(Eselon.nama, mData='nama'),
            ]
            query = DBSession.query().select_from(Eselon)
            rowTable = DataTables(request.GET, query, columns)
            return rowTable.output_result()

        elif url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            qry = Eselon.query(). \
                filter(Eselon.kode.ilike('%%%s%%' % term)). \
                order_by(Eselon.kode)

            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.kode,
                    nama=row.nama
                )
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            qry = Eselon.query(). \
                filter(Eselon.nama.ilike('%%%s%%' % term)). \
                order_by(Eselon.nama)
            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.nama,
                    kode=row.kode,
                )
                r.append(d)
            return r

    @view_config(route_name='eselon-add', renderer='templates/eselon/add.pt',
                 permission='eselon')
    def view_add(self):
        request = self.req
        form = get_form(request, AddSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form)
                save_request(request, dict(controls))
            return route_list(request)
        elif SESS_ADD_FAILED in request.session:
            return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form)
        # return dict(form=form.render())

    ########
    # Edit #
    ########   
    @view_config(route_name='eselon-edit', renderer='templates/eselon/edt.pt',
                 permission='eselon')
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
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
        form.render(appstruct=values)
        return dict(form=form)

    @view_config(route_name='eselon-view', renderer='templates/form_input.pt',
                 permission='eselon')
    def view_view(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)
        uid = row.id

        form = Form(EditSchema(), buttons=('tutup',))
        if request.POST:
            return route_list(request)
        values = row.to_dict()
        form = form.render(appstruct=values, readonly=True)
        return dict(form=form, scripts="")

    ##########
    # Delete #
    ##########
    @view_config(route_name='eselon-delete', renderer='templates/form_input.pt',
                 permission='eselon')
    def view_del(self):
        request = self.req
        q = query_id(request)
        row = q.first()

        if not row:
            return id_not_found(request)

        form = Form(EditSchema(), buttons=('hapus', 'batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'eselon ID %d %s sudah dihapus.' % (row.id, row.nama)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return route_list(request)
        form.set_appstruct(row.to_dict())
        return dict(row=row, form=form.render(readonly=True), scripts='')


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
                               'Nama %s sudah digunakan oleh kode %s' % (
                                   value['nama'], found.kode))

    # edit
    def err_ruang():
        raise colander.Invalid(form,
                               'Nama ruang %s tidak boleh lebih dari 1 karakter.' % (
                                   value['ruang']))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Eselon).filter_by(id=uid)
        eselon = q.first()
    else:
        eselon = None

    q = Eselon.query_kode(value['kode'])
    found = q.first()
    if eselon:
        if found and found.id != eselon.id:
            err_kode()
    elif found:
        err_kode()

    found = Eselon.query_nama(value['nama']).first()
    if eselon:
        if found and found.id != eselon.id:
            err_nama()
    elif found:
        err_nama()


# edit
# ruang = len(value['ruang'])
# if ruang > 1:
#     err_ruang()


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def save(values, user, row=None):
    if not row:
        row = Eselon()
        values['created'] = datetime.now()
        values['create_uid'] = user.id
    else:
        values['updated'] = datetime.now()
        values['update_uid'] = user.id
    # values['pangkat'] # TODO: pangkat
    row.from_dict(values)
    # edit
    row.updated = datetime.now()
    row.update_uid = user.id
    row.status = 'status' in values and values['status'] and 1 or 0
    row.level_id = 1

    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('eselon sudah disimpan.')


def route_list(request):
    return HTTPFound(location=request.route_url('eselon'))


def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r


########
# Edit #
########
def query_id(request):
    return DBSession.query(Eselon).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'eselon ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
