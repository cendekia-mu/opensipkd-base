import json
from datetime import datetime

import colander
from deform import (Form, widget, )
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_close, btn_add, btn_edit, btn_delete, btn_view
from pyramid.httpexceptions import (HTTPFound, )
from pyramid.view import (view_config, )
from sqlalchemy.orm import aliased

from . import widget_os
from ..models import DBSession, ResProvinsi, kategori_provinsi, flush
from ..views import ColumnDT, DataTables, BaseView
from ...detable import DeTable

SESS_ADD_FAILED = 'Tambah provinsi gagal'
SESS_EDIT_FAILED = 'Edit provinsi gagal'


@colander.deferred
def provinsi_widget(node, kw):
    values = kw.get('provinsi_list', [])
    url = node and hasattr(node, 'slave_url') and node.slave_url or ""
    slave = node and hasattr(node, 'slave') and node.slave or ""
    values.insert(0, ("", "Pilih Propinsi..."))
    return widget_os.Select2MsWidget(values=values,
                                     url=url,
                                     slave=slave,
                                     placeholder="Pilih Provinsi")


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    kategori = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=kategori_provinsi),
                                   validator=colander.Length(max=32), oid="kode")

    nama = colander.SchemaNode(colander.String(), oid="nama")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), searchable=False, orderable=False, visible=False)
    kode = colander.SchemaNode(colander.String(), width='100pt')
    nama = colander.SchemaNode(colander.String())


class ViewProvinsi(BaseView):
    def __init__(self, request):
        super(ViewProvinsi, self).__init__(request)
        self.form_scripts = ""
        self.form_params = dict(scripts="")
        self.list_route = 'provinsi'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResProvinsi

    ########
    # List #
    ########

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
            q = DBSession.query(ResProvinsi).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResProvinsi.query_kode(value['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResProvinsi.query_nama(value['nama']).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    @view_config(route_name='provinsi-view',
                 renderer='templates/form_input.pt', permission='provinsi')
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

    @view_config(route_name='provinsi',
                 renderer='templates/list_table.pt',
                 permission='provinsi')
    def view_list(self):
        table = DeTable(ListSchema(), action=f"{self.home}/provinsi",
                        buttons=(btn_view, btn_add, btn_edit, btn_delete, btn_close))
        return dict(table=table.render(), scripts="")

    ##########
    # Action #
    ##########
    @view_config(route_name='provinsi-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(ResProvinsi.id, mData='id'),
                       ColumnDT(ResProvinsi.kode, mData='kode'),
                       ColumnDT(ResProvinsi.nama, mData='nama'),
                       ColumnDT(ResProvinsi.status, mData='status'), ]
            query = DBSession.query().select_from(ResProvinsi)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()

    @view_config(route_name='provinsi-add',
                 renderer='templates/form_input.pt', permission='provinsi')
    def view_add(self):
        return super(ViewProvinsi, self).view_add()

    ########
    # Edit #
    ########
    @view_config(route_name='provinsi-edit',
                 renderer='templates/form_input.pt', permission='provinsi')
    def view_edt(self):
        return super(ViewProvinsi, self).view_edit()

    ##########
    # Delete
    ##########
    @view_config(route_name='provinsi-delete',
                 renderer='templates/form_input.pt', permission='provinsi')
    def view_delete(self):
        return super(ViewProvinsi, self).view_delete()
