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
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_delete

from ..models import (
    DBSession,
    Jabatan,
    Eselon
)
from ..views import ColumnDT, DataTables, BaseView, deferred_jenis

SESS_ADD_FAILED = 'Tambah jabatan gagal'
SESS_EDIT_FAILED = 'Edit jabatan gagal'
JENIS = ((1, 'Struktural'),
         (2, 'Fungsional'),
         (3, 'Keuangan'),
         )


def daftar_eselon():
    return DBSession.query(Eselon.id, Eselon.nama).order_by(Eselon.kode).all()


@colander.deferred
def deferred_eselon(node, kw):
    values = kw.get('daftar_eselon', [])
    return widget.SelectWidget(values=values)


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode")
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    nama_pendek = colander.SchemaNode(
        colander.String(),
        oid="nama_pendek",
        missing=colander.drop)
    nama_lain = colander.SchemaNode(
        colander.String(),
        oid="nama_lain",
        missing=colander.drop)
    jenis = colander.SchemaNode(
        colander.Integer(),
        oid="jenis",
        widget=deferred_jenis,
        title="Jenis")
    eselon_id = colander.SchemaNode(
        colander.Integer(),
        oid="eselon_id",
        widget=deferred_eselon,
        title="Eselon")
    status = colander.SchemaNode(
        colander.Boolean(),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class ViewJabatan(BaseView):
    @view_config(route_name='jabatan', renderer='templates/jabatan/list.pt',
                 permission='jabatan')
    def view_list(self):
        return dict()

    @view_config(route_name='jabatan-act', renderer='json',
                 permission='read')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict

        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(Jabatan.id, mData='id'),
                ColumnDT(Jabatan.kode, mData='kode'),
                ColumnDT(Jabatan.nama, mData='nama'),
                ColumnDT(Jabatan.nama_pendek, mData='nama_pendek'),
                ColumnDT(Eselon.nama, mData='eselon'),
                ColumnDT(Jabatan.jenis, mData='jenis'),
                ColumnDT(Jabatan.status, mData='status'),
            ]
            query = DBSession.query().select_from(Jabatan). \
                outerjoin(Eselon)
            rowTable = DataTables(request.GET, query, columns)
            return rowTable.output_result()

        elif url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            qry = DBSession.query(Jabatan). \
                filter(Jabatan.status == 1). \
                filter(Jabatan.kode.ilike('%%%s%%' % term)). \
                order_by(Jabatan.kode)

            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.nama,
                    # value = row.nama,
                    # kode  = row.kode,
                    nama=row.kode
                )
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama, Jabatan.jenis). \
                filter(Jabatan.nama.ilike('%%%s%%' % term)). \
                order_by(Jabatan.nama)
            rows = q.all()
            r = []
            for k in rows:
                if k[3] == 1:
                    nama_jenis = 'Struktural'
                elif k[3] == 2:
                    nama_jenis = 'Fungsional'
                else:
                    nama_jenis = 'Keuangan'

                d = {}
                d['id'] = k[0]
                d['value'] = k[2] + ' (' + nama_jenis + ')'
                d['kode'] = k[1]
                d['nama'] = k[2]
                r.append(d)
            return r

        elif url_dict['act'] == 'headofnama':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama, Jabatan.jenis). \
                filter(Jabatan.nama.ilike('%%%s%%' % term)). \
                order_by(Jabatan.nama)
            rows = q.all()
            r = []
            for k in rows:
                if k[3] == 1:
                    nama_jenis = 'Keuangan'
                elif k[3] == 2:
                    nama_jenis = 'Struktural'
                else:
                    nama_jenis = 'Fungsional'

                d = {}
                d['id'] = k[0]
                d['value'] = k[2] + ' (' + nama_jenis + ')'
                d['kode'] = k[1]
                d['nama'] = k[2]
                r.append(d)
            return r

    @view_config(route_name='jabatan-add', renderer='templates/form_input.pt',
                 permission='jabatan')
    def view_add(self):
        request = self.req
        form = get_form(request, AddSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), scripts="")
                save_request(request, dict(controls))
            return route_list(request)
        return dict(form=form.render(), scripts="")
        # return dict(form=form.render())

    @view_config(route_name='jabatan-edit', renderer='templates/form_input.pt',
                 permission='jabatan')
    def view_edt(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form.render(), scripts="")

                save_request(request, dict(controls), row)
            return route_list(request)

        vals = row.to_dict()
        values = {}
        for val in vals:
            if vals[val]:
                values[val] = vals[val]

        values['nama_pendek'] = row.nama_pendek or ''
        values['nama_lain'] = row.nama_lain or ''
        if not row.jenis:
            values['jenis'] = 0
        form.render(appstruct=values)
        return dict(form=form.render(), scripts="")

    @view_config(route_name='jabatan-view', renderer='templates/form_input.pt',
                 permission='jabatan')
    def view_view(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema, buttons=(btn_cancel,))
        if request.POST:
            return route_list(request)

        values = row.to_dict()
        if not row.jenis:
            values['jenis'] = 0
        form.render(appstruct=values)
        return dict(form=form.render(readonly=True), scripts="")

    @view_config(route_name='jabatan-delete', renderer='templates/form_input.pt',
                 permission='jabatan')
    def view_del(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema, buttons=(btn_delete, btn_cancel,))
        if request.POST:
            if 'delete' in request.POST:
                msg = 'Jabatan ID %d %s sudah dihapus.' % (row.id, row.nama)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return route_list(request)

        values = row.to_dict()
        if not row.jenis:
            values['jenis'] = 0
        form.render(appstruct=values)
        return dict(form=form.render(readonly=True), scripts="")


def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
                               'Kode %s sudah digunakan oleh %s' % (
                                   value['kode'], found.nama))

    def err_nama():
        raise colander.Invalid(form,
                               'Uraian %s sudah digunakan oleh kode %s' % (
                                   value['nama'], found.kode))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Jabatan).filter_by(id=uid)
        jabatan = q.first()
    else:
        jabatan = None

    q = Jabatan.query_kode(value['kode'])  # DBSession.query(Jabatan).filter_by(kode=value['kode'])
    found = q.first()
    if jabatan:
        if found and found.id != jabatan.id:
            err_kode()
    elif found:
        err_kode()

    found = Jabatan.query_nama(value['nama']).first()
    if jabatan:
        if found and found.id != jabatan.id:
            err_nama()
    elif found:
        err_nama()


def get_form(request, class_form, row=None, buttons=(btn_save, btn_cancel)):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_jenis=JENIS,
                         daftar_eselon=daftar_eselon(),
                         )
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=buttons)


def save(values, user, row=None):
    if not row:
        row = Jabatan()
        values['created'] = datetime.now()
        values['create_uid'] = user.id
    else:
        values['updated'] = datetime.now()
        values['update_uid'] = user.id

    values['status'] = 'status' in values and values['status'] and 1 or 0

    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Jabatan sudah disimpan.')


def route_list(request):
    return HTTPFound(location=request.route_url('jabatan'))



def query_id(request):
    return DBSession.query(Jabatan).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'Jabatan ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
