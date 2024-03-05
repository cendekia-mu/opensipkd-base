import colander
from deform import (widget, )
from pyramid.view import (view_config, )
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from opensipkd.models import DBSession as PartnerDBSession, DBSession, \
    ResCompany
from opensipkd.models import Departemen, Jabatan
from opensipkd.models import Partner, PartnerDepartemen
from opensipkd.tools import dmy, date_from_str
from . import widget_os
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah posisi partner gagal'
SESS_EDIT_FAILED = 'Edit posisi partner gagal'


class AddSchema(colander.Schema):
    nama_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/partner/hon/act',
        min_length=2,
        style="z-index: 100000 !important;")

    departemen_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/departemen/hon/act',
        min_length=2,

        style="z-index: 100001 !important;")


    jabatan_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/jabatan/hon/act',
        min_length=2,

        style="z-index: 99999 !important;")

    partner_id = colander.SchemaNode(
        colander.Integer(),
        oid="partner_id",
        widget=widget.HiddenWidget(),
    )

    nama = colander.SchemaNode(
        colander.String(),
        widget=nama_widget,
        oid="partner_nm")
    departemen_id = colander.SchemaNode(
        colander.Integer(),
        oid="departemen_id",
        widget=widget.HiddenWidget(),
    )
    departemen = colander.SchemaNode(
        colander.String(),
        widget=departemen_widget,
        oid="departemen_nm")
    jabatan_id = colander.SchemaNode(
        colander.Integer(),
        oid="jabatan_id",
        widget=widget.HiddenWidget(),
    )
    jabatan = colander.SchemaNode(
        colander.String(),
        widget=jabatan_widget,
        oid="jabatan_nm",
        title="Jabatan")
    mulai = colander.SchemaNode(
        colander.String(),
        oid="mulai",
        widget=widget_os.DateInputWidget(css_class="date", format="dd-mm-yyyy"))
    selesai = colander.SchemaNode(
        colander.String(),
        oid="selesai",
        widget=widget_os.DateInputWidget(css_class="date", format="dd-mm-yyyy",
                                         style="z-index: 9999 !important;"))


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), title="Action")
    nama = colander.SchemaNode(
        colander.String(), field=Partner.nama)
    mulai = colander.SchemaNode(
        colander.String())
    selesai = colander.SchemaNode(
        colander.String())


class ViewPartner(BaseView):
    def __init__(self, request):
        super(ViewPartner, self).__init__(request)
        self.list_schema = ListSchema
        self.table = PartnerDepartemen
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        # self.form_scripts = """
        # $(document).ready(function () {
        #
        #     $('#pegawai_nm').typeahead({
        #         "hint"     : true,
        #         "highlight": true,
        #         "minLength": 1,
        #         "remote"   : {
        #                 url: "/partner/hon/act?term=%QUERY",
        #                 beforeSend: function () {
        #                     $('#partner_nm').addClass("loading");
        #                 },
        #                 filter: function(parsedResponse){
        #                     $('#partner_nm').removeClass('loading');
        #                     return parsedResponse;
        #                 }
        #         },
        #     },{
        #         "name"      : 'partner_nm',
        #         "displayKey": 'value',
        #     });
        #
        #     $('#partner_nm').bind('typeahead:selected', function(obj, datum, name) {
        #       $('#partner_id').val(datum.id);
        #       $('#partner_nm').val(datum.nama);
        #     });
        #
        #     $('#departemen_nm').typeahead({
        #         "hint"     : true,
        #         "highlight": true,
        #         "minLength": 1,
        #         "remote"   : {
        #                 url: "/departemen/hon/act?term=%QUERY",
        #                 beforeSend: function () {
        #                     $('#departemen_nm').addClass("loading");
        #                 },
        #                 filter: function(parsedResponse){
        #                     $('#departemen_nm').removeClass('loading');
        #                     return parsedResponse;
        #                 }
        #         },
        #     },{
        #         "name"      : 'departemen_nm',
        #         "displayKey": 'value',
        #     });
        #
        #     $('#departemen_nm').bind('typeahead:selected', function(obj, datum, name) {
        #       $('#departemen_id').val(datum.id);
        #     });
        #
        #
        #
        #     $('#jabatan_nm').typeahead({
        #         "hint"     : true,
        #         "highlight": true,
        #         "minLength": 1,
        #         "remote"   : {
        #                 url: "/partner/departemen/hon_jabatannm/act?term=%QUERY",
        #                 beforeSend: function () {
        #                     $('#jabatan_nm').addClass("loading");
        #                 },
        #                 filter: function(parsedResponse){
        #                     $('#jabatan_nm').removeClass('loading');
        #                     return parsedResponse;
        #                 }
        #         },
        #     },{
        #         "name"      : 'jabatan_nm',
        #         "displayKey": 'value',
        #     });
        #
        #     $('#jabatan_nm').bind('typeahead:selected', function(obj, datum, name) {
        #       $('#jabatan_id').val(datum.id);
        #       $('#jabatan_nm').val(datum.value);
        #
        #     });
        # });
        # """
        #
        # self.list_col_defs = json.dumps(
        #     [{"searchable": False, "visible": False, "targets": [0], }, {
        #         "searchable": True, "orderable": True, "targets": [1, 2],
        #     }])
        # self.list_cols = [{'title': "ID", 'data': "id"},
        #                   {'title': "NIP", 'data': "nik", 'width': '100pt'},
        #                   {'title': "Nama", 'data': "nama"},
        #                   {'title': "Unit Kerja", 'data': "departemen"},
        #                   {'title': "Jabatan", 'data': "jabatan"},
        #                   {'title': "Pemda", 'data': "jenis"},
        #                   {'title': "Mulai", 'data': "mulai"},
        #                   {'title': "Selesai", 'data': "selesai"}, ]
        # self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
        #                     'btn_close'
        # self.form_params = dict(scripts="")
        # self.list_url = 'partner/departemen'
        self.list_route = 'partner-departemen'

    def form_validator(self, form, value):
        def err_partner():
            raise colander.Invalid(form,
                                   'Partner Belum Dipilih')

        def err_departemen():
            raise colander.Invalid(form,
                                   'Departemen Kerja Belum Dipilih')

        def err_jabatan():
            raise colander.Invalid(form,
                                   'Partner Belum Dipilih')

        if not value['jabatan_id']:
            err_jabatan()
        elif not value['departemen_id']:
            err_departemen()
        elif not value['partner_id']:
            err_partner()

    def save_request(self, values, row=None):
        request = self.req
        if 'id' in request.matchdict:
            values['id'] = request.matchdict['id']
        if 'mulai' in values:
            if values['mulai']:
                values['mulai'] = date_from_str(values['mulai'])
            else:
                values['mulai'] = None
        if 'selesai' in values:
            if values['selesai']:
                values['selesai'] = date_from_str(values['selesai'])
            else:
                values['selesai'] = None
        query_struktural = DBSession.query(Jabatan.jenis). \
            filter(Jabatan.id == values['jabatan_id']).scalar()
        values['jabatan_id'] = query_struktural
        row = self.save(values, request.user, row)
        request.session.flash('Posisi Partner sudah disimpan.')
        return row

    @view_config(route_name='partner-departemen', renderer='templates/form.pt',
                 permission='view')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='partner-departemen-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        struktural = aliased(Jabatan)
        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(PartnerDepartemen.id, mData='id'),
                ColumnDT(Partner.kode, mData='nik'),
                ColumnDT(Partner.nama, mData='nama'),
                ColumnDT(Departemen.nama, mData='departemen'),
                ColumnDT(Jabatan.nama, mData='jabatan'),
                ColumnDT(ResCompany.nama, mData='jenis'),
                ColumnDT(struktural.nama, mData='struktural_nm'),
                ColumnDT(PartnerDepartemen.mulai, mData='mulai'),
                ColumnDT(PartnerDepartemen.selesai, mData='selesai'),
            ]
            q = PartnerDBSession.query().select_from(PartnerDepartemen) \
                .join(Departemen,
                      PartnerDepartemen.departemen_id == Departemen.id) \
                .outerjoin(ResCompany, Departemen.company_id == ResCompany.id) \
                .outerjoin(Partner, Partner.id == PartnerDepartemen.partner_id) \
                .outerjoin(Jabatan,
                           (PartnerDepartemen.jabatan_id == Jabatan.id)) \
                .outerjoin(struktural,
                           (PartnerDepartemen.jabatan_id == struktural.id)) \
                .order_by(Partner.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            row_table = DataTables(request.GET, q, columns)

            return row_table.output_result()

        elif url_dict['act'] == 'hon_departemen':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
                                       PartnerDepartemen.jabatan_id,
                                       Jabatan.nama.label('jabatan_nm'),
                                       ). \
                join(PartnerDepartemen). \
                join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
                filter(or_(Jabatan.kode == '101', Jabatan.kode == '102')). \
                order_by(Partner.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)

            rows = q.all()
            r = []
            keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
            for k in rows:
                values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
                r.append(dict(zip(keys, values)))
            return r

        elif url_dict['act'] == 'hon_jabatan':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            partner_id = 'partner_id' in params and params['partner_id'] or 0
            # filter(or_(Jabatan.kode == '103', Jabatan.kode == '104')) dilepas sementara
            q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
                                       PartnerDepartemen.jabatan_id,
                                       Jabatan.nama.label('jabatan_nm'),
                                       ). \
                join(PartnerDepartemen). \
                join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
                order_by(Partner.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            rows = q.all()
            r = []
            keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
            for k in rows:
                values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
                r.append(dict(zip(keys, values)))
            return r

        elif url_dict['act'] == 'hon_skpkd':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
                                       PartnerDepartemen.jabatan_id,
                                       Jabatan.nama.label('jabatan_nm'),
                                       ). \
                join(PartnerDepartemen). \
                join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
                filter(or_(Jabatan.kode == '101', Jabatan.kode == '102',
                           Jabatan.kode == '103', Jabatan.kode ==
                           '104')). \
                order_by(Partner.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            rows = q.all()
            r = []
            keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
            for k in rows:
                values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
                r.append(dict(zip(keys, values)))
            return r

        elif url_dict['act'] == 'hon_jabatannm':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama,
                                Jabatan.jenis). \
                filter(Jabatan.nama.ilike('%%%s%%' % term)). \
                order_by(Jabatan.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
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

    def get_values(self, row, istime=False):
        values = super().get_values(row, istime)
        values['nama'] = row.partner.nama
        values['jabatan'] = row.jabatan.nama
        values['departemen'] = row.departemen.nama
        values['mulai'] = dmy(row.mulai)
        values['selesai'] = dmy(row.selesai)
        if not row.jabatan_id:
            values['jabatan_id'] = 0
        else:
            jb = Jabatan.query_id(row.jabatan_id).first()
            if jb:
                values['struktural_nm'] = jb.nama

        return values

    @view_config(route_name='partner-departemen-view',
                 renderer='templates/form.pt', permission='partner-departemen')
    def view_view(self):  # row = query_id(request).first()
        return super().view_view()

    def before_add(self):
        values = {'departemen_id': self.ses['departemen_id'],
                  'departemen_nm': self.ses['departemen_nm'],
                  'departemen_kd': self.ses['departemen_kd']}
        return values

    @view_config(route_name='partner-departemen-add',
                 renderer='templates/form.pt',
                 permission='partner-departemen')
    def view_add(self):
        return super().view_add()

    @view_config(route_name='partner-departemen-edit',
                 renderer='templates/form.pt',
                 permission='partner-departemen')
    def view_edt(self):
        return super().view_edit()

    @view_config(route_name='partner-departemen-delete',
                 renderer='templates/form.pt',
                 permission='partner-departemen')
    def view_del(self):
        return super().view_delete()
