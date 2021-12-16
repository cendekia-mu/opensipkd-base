import json

import colander
from deform import (widget, Form, )
from opensipkd.tools.buttons import btn_close, btn_cancel, btn_save
from pyramid.view import (view_config, )

from .kecamatan import kecamatan_widget
from ..models import DBSession, ResDesa, kategori_desa, ResKecamatan
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah desa gagal'
SESS_EDIT_FAILED = 'Edit desa gagal'


@colander.deferred
def desa_widget(node, kw):
    values = kw.get('desa_list', [])
    return widget.Select2Widget(values=values)


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


class ViewDesa(BaseView):
    def __init__(self, request):
        super(ViewDesa, self).__init__(request)
        self.form_scripts = ""
        self.list_col_defs = json.dumps(
            [{"searchable": False, "visible": False, "targets": [0], }, {
                "searchable": True, "orderable": True, "targets": [1, 2],
            }])
        self.list_cols = [{'title': "ID", 'data': "id"},
                          {'title': "Kecamatan", 'data': "kecamatan", 'width': '200pt'},
                          {'title': "Kode", 'data': "kode", 'width': '100pt'},
                          {'title': "Nama", 'data': "nama"}, ]
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        self.list_url = 'desa'
        self.list_route = 'desa'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResDesa

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

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel)):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(request=self.req,
                             kecamatan_list=ResKecamatan.get_list())
        schema.request = self.req
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons)

    @view_config(route_name='desa-view',
                 renderer='templates/form_input.pt', permission='desa')
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
                 renderer='templates/list.pt',
                 permission='desa')
    def view_list(self):
        return super().view_list()

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
                       ColumnDT(ResKecamatan.nama, mData='kecamatan'),]
            query = DBSession.query().select_from(ResDesa) \
                .join(ResKecamatan, ResKecamatan.id == ResDesa.kecamatan_id)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()
        elif url_dict['act'] == 'select':
            kecamatan_id = request.params["kecamatan_id"]
            data = ResKecamatan.get_list(kecamatan_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result


    @view_config(route_name='desa-add',
                 renderer='templates/form_input.pt', permission='desa')
    def view_add(self):
        return super(ViewDesa, self).view_add()

    ########
    # Edit #
    ########
    @view_config(route_name='desa-edit',
                 renderer='templates/form_input.pt', permission='desa')
    def view_edt(self):
        return super(ViewDesa, self).view_edit()

    ##########
    # Delete
    ##########
    @view_config(route_name='desa-delete',
                 renderer='templates/form_input.pt', permission='desa')
    def view_delete(self):
        return super(ViewDesa, self).view_delete()
