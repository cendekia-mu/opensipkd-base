import json

import colander
from deform import (widget, Form, ValidationFailure, )
from opensipkd.tools.buttons import btn_close, btn_cancel, btn_save
from pyramid.view import (view_config, )

from opensipkd.base.models import ResProvinsi, ResDati2, ResDesa
from .partner_base import PartnerSchema
from ..models import DBSession, ResCompany, ResKecamatan, Partner
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah pemda gagal'
SESS_EDIT_FAILED = 'Edit pemda gagal'


@colander.deferred
def company_widget(node, kw):
    values = kw.get('company_list', [])
    values.insert(0, ("", "Select Pemda"))
    return widget.Select2Widget(values=values,
                                placeholder="Pilih Organisasi")


class AddSchema(PartnerSchema):
    def after_bind(self, node, kw):
        self["email"].missing = colander.drop


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))
    partner_id = colander.SchemaNode(colander.Integer(),
                                     widget=widget.HiddenWidget(),
                                     missing=colander.drop,
                                     oid="partner_id")


class ViewCompany(BaseView):
    def __init__(self, request):
        super(ViewCompany, self).__init__(request)
        self.form_scripts = ""
        self.list_col_defs = json.dumps(
            [{"searchable": False, "visible": False, "targets": [0], }, {
                "searchable": True, "orderable": True, "targets": [1, 2],
            }])
        self.list_cols = [{'title': "ID", 'data': "id"},
                          {'title': "Kode", 'data': "kode", 'width': '100pt'},
                          {'title': "Nama", 'data': "nama"}, ]
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        # self.list_url = 'company'
        self.list_route = 'company'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResCompany

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
            q = DBSession.query(ResCompany).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResCompany.query_kode(value['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResCompany.query_nama(value['nama']).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel)):
        schema = class_form(validator=self.form_validator)
        provinsi_list = ResProvinsi.get_list()
        dati2_list = row and row.provinsi_id and ResDati2.get_list(row.provinsi_id) or []
        kecamatan_list = row and row.dati2_id and ResKecamatan.get_list(row.dati2_id) or []
        desa_list = row and row.kecamatan_id and ResDesa.get_list(row.kecamatan_id) or []
        schema = schema.bind(provinsi_list=provinsi_list,
                             dati2_list=dati2_list,
                             kecamatan_list=kecamatan_list,
                             desa_list=desa_list
                             )
        schema.request = self.req
        return Form(schema, buttons=buttons)

    @view_config(route_name='company-view',
                 renderer='templates/form_input.pt', permission='company')
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

    @view_config(route_name='company',
                 renderer='templates/list.pt',
                 permission='company')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='company-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(ResCompany.id, mData='id'),
                       ColumnDT(ResCompany.kode, mData='kode'),
                       ColumnDT(ResCompany.nama, mData='nama'), ]
            query = DBSession.query().select_from(ResCompany)
            if request.user.company_id:
                query = query.filter_by(id=request.user.company_id)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()

    @view_config(route_name='company-add',
                 renderer='templates/form_input.pt', permission='company')
    def view_add(self):
        if self.req.user.company_id:
            return self.route_list("Hak Akses Terbatas", "error")
        return super(ViewCompany, self).view_add()

    ########
    # Edit #
    ########
    @view_config(route_name='company-edit',
                 renderer='templates/form_input.pt', permission='company')
    def view_edt(self):
        row = self.query_id().first()
        if not row:
            return self.id_not_found()
        part = Partner.query_id(row.partner_id).first()
        form = self.get_form(self.edit_schema, row=part)
        if self.req.POST:
            if 'save' in self.req.POST:
                controls = self.req.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)

                self.save_request(dict(controls), row)
            return self.route_list()

        values = part and part.to_dict() or {}
        values.update(row.to_dict())
        form.set_appstruct(values)
        return dict(form=form.render(), scripts=self.form_scripts)

    @view_config(route_name='company-delete',
                 renderer='templates/form_input.pt', permission='company')
    def view_delete(self):
        return super(ViewCompany, self).view_delete()

    def save_request(self, values, row=None):
        if 'partner_id' in values:
            part = Partner.query_id(values['partner_id']).first()
            values["id"] = part.id
        else:
            part = None
            if "id" in values:
                del values["id"]
        from .partner import save as partner_save
        part = partner_save(values, self.req.user, part)
        if part:
            values["partner_id"] = part.id
        if "id" in self.req.matchdict:
            values["id"] = self.req.matchdict["id"]

        row = self.save(values, self.req.user, row)
        return row

    def query_id(self):
        q = DBSession.query(self.table).filter_by(
            id=self.req.matchdict['id'])
        if self.req.user.company_id:
            q = q.filter_by(id=self.req.user.company_id)
        return q