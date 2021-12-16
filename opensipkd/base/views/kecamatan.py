import json

import colander
from deform import (widget, Form, )
from opensipkd.tools.buttons import btn_close, btn_cancel, btn_save
from pyramid.view import (view_config, )

from . import widget_os
from .dati2 import dati2_widget
from ..models import DBSession, ResKecamatan, ResDati2
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah kecamatan gagal'
SESS_EDIT_FAILED = 'Edit kecamatan gagal'


@colander.deferred
def kecamatan_widget(node, kw):
    default_url = "/desa/select/act?kecamatan_id="
    default_slave = "desa_id"
    values = kw.get('kecamatan_list', [])
    url = kw.get('kecamatan_url', [])
    slave = kw.get('kecamatan_slave', [])
    if not url:
        url = default_url
    if not slave:
        slave = default_slave
    values.insert(0, ("", "Pilih Kecamatan..."))

    return widget_os.Select2MsWidget(values=values,
                                     url=url,
                                     slave=slave,
                                     placeholder="Pilih Kecamatan")


class AddSchema(colander.Schema):
    dati2_id = colander.SchemaNode(colander.String(),
                                      widget=dati2_widget,
                                      validator=colander.Length(max=32), oid="kode")
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    nama = colander.SchemaNode(colander.String(), oid="nama")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ViewDati2(BaseView):
    def __init__(self, request):
        super(ViewDati2, self).__init__(request)
        self.form_scripts = ""
        self.list_col_defs = json.dumps(
            [{"searchable": False, "visible": False, "targets": [0], }, {
                "searchable": True, "orderable": True, "targets": [1, 2],
            }])
        self.list_cols = [{'title': "ID", 'data': "id"},
                          {'title': "Kab/Kota", 'data': "dati2", 'width': '200pt'},
                          {'title': "Kode", 'data': "kode", 'width': '100pt'},
                          {'title': "Nama", 'data': "nama"}, ]
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        self.list_url = 'kecamatan'
        self.list_route = 'kecamatan'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResKecamatan

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
            q = DBSession.query(ResKecamatan).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResKecamatan.query_kode(value['kode']) \
            .filter(ResKecamatan.dati2_id == value["dati2_id"])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResKecamatan.query_nama(value['nama']) \
            .filter(ResKecamatan.dati2_id == value["dati2_id"]).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel)):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(request=self.req,
                             dati2_list=ResDati2.get_list())
        schema.request = self.req
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons)

    @view_config(route_name='kecamatan-view',
                 renderer='templates/form_input.pt', permission='kecamatan')
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

    @view_config(route_name='kecamatan',
                 renderer='templates/list.pt',
                 permission='kecamatan')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='kecamatan-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(ResKecamatan.id, mData='id'),
                       ColumnDT(ResKecamatan.kode, mData='kode'),
                       ColumnDT(ResKecamatan.nama, mData='nama'),
                       ColumnDT(ResKecamatan.status, mData='status'),
                       ColumnDT(ResDati2.nama, mData='dati2'),]
            query = DBSession.query().select_from(ResKecamatan) \
                .join(ResDati2, ResDati2.id == ResKecamatan.dati2_id)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()
        elif url_dict['act'] == 'select':
            dati2_id = request.params["dati2_id"]
            data = ResKecamatan.get_list(dati2_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result


    @view_config(route_name='kecamatan-add',
                 renderer='templates/form_input.pt', permission='kecamatan')
    def view_add(self):
        return super(ViewDati2, self).view_add()

    ########
    # Edit #
    ########
    @view_config(route_name='kecamatan-edit',
                 renderer='templates/form_input.pt', permission='kecamatan')
    def view_edt(self):
        return super(ViewDati2, self).view_edit()

    ##########
    # Delete
    ##########
    @view_config(route_name='kecamatan-delete',
                 renderer='templates/form_input.pt', permission='kecamatan')
    def view_delete(self):
        return super(ViewDati2, self).view_delete()
