import logging

import colander
from datatables import ColumnDT
from deform import (widget, )
from pyramid.view import (view_config, )
from sqlalchemy.orm import aliased

from opensipkd.models import DBSession, ResCompany, ResKecamatan, Partner
from opensipkd.models import ResProvinsi, ResDati2, ResDesa, User
from . import DataTables
from .partner_base import PartnerSchema
from .. import get_urls
from ..views import BaseView

log = logging.getLogger(__name__)
SESS_ADD_FAILED = 'Tambah pemda gagal'
SESS_EDIT_FAILED = 'Edit pemda gagal'


@colander.deferred
def company_widget(node, kw):
    values = kw.get('company_list', [])
    values.insert(0, ("", "Select Pemda"))
    return widget.Select2Widget(values=values,
                                placeholder="Pilih Organisasi")


class AddSchema(PartnerSchema):
    parent_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(), oid="parent_id", missing=colander.drop,
    )

    parent_nm = colander.SchemaNode(
        colander.String(), missing=colander.drop,
        widget=widget.AutocompleteInputWidget(
            size=60, min_length=3,
            requirements=(("typeahead", None), ("deform", None),
                          {"js": "opensipkd.base:static/js/form/company.js"})
        ),
        oid="parent_nm", title="Induk")

    def after_bind(self, node, kw):
        self["email"].missing = colander.drop
        request = kw["request"]
        self["parent_nm"].widget = widget.AutocompleteInputWidget(
            size=60, min_length=3,
            requirements=(("typeahead", None), ("deform", None),
                          {"js": "opensipkd.base:static/js/form/company.js"}),
            values=get_urls(f"{request.route_url('company')}/hon/act"))


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True),
                             visible=False, )
    partner_id = colander.SchemaNode(colander.Integer(),
                                     widget=widget.HiddenWidget(),
                                     missing=colander.drop,
                                     oid="partner_id")


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="Action")
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode",
        title="Kode",
        width="100pt")
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama")
    parent_nm = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="parent_nm",
        field="alias.nama"

    )

    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(),
        oid="status")


class ViewCompany(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_route = 'company'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.list_schema = ListSchema
        self.table = ResCompany

    def form_validator(self, form, value):
        err = colander.Invalid(form, "")

        def err_kode():
            msg = f"Kode {value['kode']} sudah digunakan oleh {found.nama}"
            err["kode"] = msg
            raise err

        def err_nama():
            err["nama"] = f"Uraian {value['nama']} sudah digunakan oleh kode {found.kode}"
            raise err

        def err_email():
            err["email"] = f"Email {value['email']} sudah digunakan oleh kode {found.nama}"
            raise err

        def err_user():
            err["email"] = f"Email {value['email']} sudah digunakan oleh kode {found.user_name}"
            raise err

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(ResCompany).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = self.table.query_kode(value['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = self.table.query_nama(value['nama']).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

        partner_id = value.get('partner_id')

        if 'email' in value and value["email"]:
            found = Partner.query_email(value.get('email')).first()
            if found:
                if found and found.id != partner_id:
                    err_email()
            elif found:
                err_email()

            found = User.get_by_identity(value.get('email'))
            if found:
                err_user()
        value["status"] = "status" in value and value["status"] and 1 or 0
        value["is_vendor"] = "is_vendor" in value and value["is_vendor"] and 1 or 0
        value["is_customer"] = "is_customer" in value and value["is_customer"] and 1 or 0

    def get_bindings(self, row=None):
        provinsi_list = ResProvinsi.get_list()
        partner = row and row.partner or None
        dati2_list = partner and partner.provinsi_id and ResDati2.get_list(
            partner.provinsi_id) or []
        kecamatan_list = partner and partner.dati2_id and ResKecamatan.get_list(
            partner.dati2_id) or []
        desa_list = partner and partner.kecamatan_id and ResDesa.get_list(
            partner.kecamatan_id) or []
        return dict(provinsi_list=provinsi_list,
                    dati2_list=dati2_list,
                    kecamatan_list=kecamatan_list,
                    desa_list=desa_list
                    )

    @view_config(route_name='company-view',
                 renderer='templates/form.pt', permission='company')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='company',
                 renderer='templates/table.pt',
                 permission='company')
    def view_list(self):
        return super().view_list()

    def filter_company(self, query):
        if self.req.user.company_id:
            return query.filter(
                self.table.id == self.req.user.company_id)
        return query

    @view_config(route_name='company-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        alias = aliased(ResCompany)
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(self.table.id, mData='id'),
                       ColumnDT(self.table.kode, mData='kode'),
                       ColumnDT(self.table.nama, mData='nama'),
                       ColumnDT(alias.nama, mData='parent_nm'),
                       ColumnDT(self.table.status, mData='status'),
                       # ColumnDT(Departemen.level_id, mData='level_id'),
                       ]
            query = DBSession.query().select_from(ResCompany).outerjoin(
                alias, ResCompany.parent_id == alias.id)
            query = self.filter_company(query)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()
        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(self.table) \
                .filter(self.table.status == 1,
                        self.table.nama.ilike('%%%s%%' % term)) \
                .order_by(self.table.nama)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama)
                r.append(d)
            log.error(r)
            return r

    @view_config(route_name='company-add',
                 renderer='templates/form.pt', permission='company')
    def view_add(self):
        return super(ViewCompany, self).view_add()

    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        partner = row.partner
        if partner:
            p = partner.to_dict()
            del p["id"]
            d.update(p)

        if "parent_id" in d and d["parent_id"]:
            parent = ResCompany.query_id(d["parent_id"]).first()
            if parent:
                d["parent_nm"] = parent.nama
        return d

    @view_config(route_name='company-edit',
                 renderer='templates/form.pt', permission='company')
    def view_edit(self):
        return super(ViewCompany, self).view_edit()

    @view_config(route_name='company-delete',
                 renderer='templates/form_input.pt', permission='company')
    def view_delete(self):
        return super(ViewCompany, self).view_delete()

    def save_request(self, values, row=None):
        # Save Partner First
        parent_id = "parent_id" in values and values["parent_id"] or None
        if parent_id:
            del values["parent_id"]

        if 'partner_id' in values:
            part = Partner.query_id(values['partner_id']).first()
            values["id"] = part.id
        else:
            part = None
            if "id" in values:
                del values["id"]
        if not part:
            part = Partner()
        part.from_dict(values)
        DBSession.add(part)
        DBSession.flush()

        # Save Company
        if part:
            values["partner_id"] = part.id
        if parent_id:
            values["parent_id"] = parent_id

        if "id" in self.req.matchdict:
            values["id"] = self.req.matchdict["id"]

        row = self.save(values, self.req.user, row)
        if not part.company_id:
            part.company_id = row.id
            DBSession.add(part)
            DBSession.flush()
        return row
