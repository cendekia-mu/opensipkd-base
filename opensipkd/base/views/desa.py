import json

import colander
from deform import (widget, Form, )
from opensipkd.tools.buttons import btn_close, btn_cancel, btn_save, btn_add, btn_edit, btn_delete
from pyramid.view import (view_config, )

from .kecamatan import kecamatan_widget
from ..models import DBSession, ResDesa, kategori_desa, ResKecamatan
from ..views import ColumnDT, DataTables, BaseView
from ...detable import DeTable

SESS_ADD_FAILED = 'Tambah desa gagal'
SESS_EDIT_FAILED = 'Edit desa gagal'


@colander.deferred
def desa_widget(node, kw):
    values = kw.get('desa_list', [])
    return widget.Select2Widget(values=values,
                                placeholder="Pilih Desa/Kelurahan")


class AddSchema(colander.Schema):
    kecamatan_id = colander.SchemaNode(colander.String(),
                                       widget=kecamatan_widget,
                                       validator=colander.Length(max=32), oid="kode")
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    kategori = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=kategori_desa),
                                   validator=colander.Length(max=32), oid="kode")

    nama = colander.SchemaNode(colander.String(), oid="nama")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), searchable=False, orderable=False, visible=False)
    kode = colander.SchemaNode(colander.String(), width='100pt', title="Kode")
    nama = colander.SchemaNode(colander.String(), title="Nama")
    kecamatan = colander.SchemaNode(colander.String())
    status = colander.SchemaNode(colander.Integer(), width="30pt")


class ViewDesa(BaseView):
    def __init__(self, request):
        super(ViewDesa, self).__init__(request)
        self.form_scripts = ""
        self.form_params = dict(scripts="")
        self.list_url = 'desa'
        self.list_route = 'desa'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResDesa
        self.list_schema = ListSchema

    def form_validator(self, form, value):
        def err_kode():
            raise colander.Invalid(form, 'Kode %s sudah digunakan oleh %s' % (
                value['kode'], found.nama))

        def err_nama():
            raise colander.Invalid(form,
                                   'Uraian %s sudah digunakan oleh kode %s' % (
                                       value['nama'], found.kode))

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(ResDesa).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResDesa.query_kode(value['kode']) \
            .filter(ResDesa.kecamatan_id == value["kecamatan_id"])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResDesa.query_nama(value['nama']) \
            .filter(ResDesa.kecamatan_id == value["kecamatan_id"]).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    def get_bindings(self, row=None):
        return dict(request=self.req,
                    kecamatan_list=ResKecamatan.get_list())


    @view_config(route_name='desa-view',
                 renderer='templates/form.pt', permission='desa')
    def view_view(self):  # row = query_id(request).first()
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()

        form = self.get_form(EditSchema, buttons=(btn_close,))
        if request.POST:
            return self.route_list()

        form.set_appstruct(self.get_values(row))
        return dict(form=form.render(readonly=True), scripts=self.form_scripts)

    @view_config(route_name='desa',
                 renderer='templates/table.pt',
                 permission='desa')
    def view_list(self):
        return super(ViewDesa, self).view_list()

    @view_config(route_name='desa-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(ResDesa.id, mData='id'),
                       ColumnDT(ResDesa.kode, mData='kode'),
                       ColumnDT(ResDesa.nama, mData='nama'),
                       ColumnDT(ResDesa.status, mData='status'),
                       ColumnDT(ResKecamatan.nama, mData='kecamatan'), ]
            query = DBSession.query().select_from(ResDesa) \
                .join(ResKecamatan, ResKecamatan.id == ResDesa.kecamatan_id)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()
        elif url_dict['act'] == 'select':
            kecamatan_id = request.params["kecamatan_id"]
            data = ResDesa.get_list(kecamatan_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result

    @view_config(route_name='desa-add',
                 renderer='templates/form.pt', permission='desa')
    def view_add(self):
        return super(ViewDesa, self).view_add()

    @view_config(route_name='desa-edit',
                 renderer='templates/form.pt', permission='desa')
    def view_edt(self):
        return super(ViewDesa, self).view_edit()

    @view_config(route_name='desa-delete',
                 renderer='templates/form.pt', permission='desa')
    def view_delete(self):
        return super(ViewDesa, self).view_delete()
