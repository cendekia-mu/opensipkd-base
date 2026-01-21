import colander
from deform import (widget, )
from sqlalchemy import Boolean, or_
from sqlalchemy.orm import aliased

from opensipkd.base.models import DBSession as PartnerDBSession, DBSession
from opensipkd.base.models import Departemen, Jabatan
from opensipkd.base.models import Partner, PartnerDepartemen
from opensipkd.base.widgets import widget_os
from opensipkd.tools import dmy, date_from_str
from ..views import ColumnDT, DataTables, BaseView

class AddSchema(colander.Schema):
    nama_widget = widget.AutocompleteInputWidget(
        size=60,
        min_length=2,
        # style="z-index: 100001 !important;"
        )
    departemen_widget = widget.AutocompleteInputWidget(
        size=60,
        min_length=2,
        # style="z-index: 100000 !important;"
        )
    jabatan_widget = widget.AutocompleteInputWidget(
        size=60,
        min_length=2,
        # style="z-index: 99999 !important;"
        )
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
    )
    mulai = colander.SchemaNode(
        colander.String(),
        oid="mulai",
        widget=widget_os.BootStrapDateInputWidget()
    )
    selesai = colander.SchemaNode(
        colander.String(),
        oid="selesai",
        widget=widget_os.BootStrapDateInputWidget()
    )
    widget = widget.FormWidget(

        requirements=(("deform", None), 
                      {
                      "js": "opensipkd.base:static/js/form/posisi.js"}),
    )

    def after_bind(self, schema, kw):
        request = kw.get('request')
        schema["nama"].widget.values = request.route_url(
            'base-partner-departemen-act', act="partner")
        schema["departemen"].widget.values = request.route_url(
            'base-departemen-act', act="hon")
        schema["jabatan_id"].widget = widget.Select2Widget(
            values = [(r.id, r.nama) for r in Jabatan.query().order_by(Jabatan.nama)]
        )

        # if request:
        #     ses = request.session
        #     if 'departemen_id' in ses:
        #         self.departemen_id.default = ses['departemen_id']
        #     if 'departemen_nm' in ses:
        #         self.departemen.default = ses['departemen_nm']
        #     if 'departemen_kd' in ses:
        #         self.departemen_kd = ses['departemen_kd']

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


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_schema = ListSchema
        self.table = PartnerDepartemen
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.list_route = 'base-partner-departemen'

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

    # def view_act(self):
    #     request = self.req
    #     ses = request.session
    #     params = request.params
    #     url_dict = request.matchdict
    #     struktural = aliased(Jabatan)
    #     if url_dict['act'] == 'grid':
    #         columns = [
    #             ColumnDT(PartnerDepartemen.id, mData='id'),
    #             ColumnDT(Partner.kode, mData='nik'),
    #             ColumnDT(Partner.nama, mData='nama'),
    #             ColumnDT(Departemen.nama, mData='departemen'),
    #             ColumnDT(Jabatan.nama, mData='jabatan'),
    #             ColumnDT(struktural.nama, mData='struktural_nm'),
    #             ColumnDT(PartnerDepartemen.mulai, mData='mulai'),
    #             ColumnDT(PartnerDepartemen.selesai, mData='selesai'),
    #         ]
    #         q = PartnerDBSession.query().select_from(PartnerDepartemen) \
    #             .join(Departemen,
    #                   PartnerDepartemen.departemen_id == Departemen.id) \
    #             .outerjoin(Partner, Partner.id == PartnerDepartemen.partner_id) \
    #             .outerjoin(Jabatan,
    #                        (PartnerDepartemen.jabatan_id == Jabatan.id)) \
    #             .outerjoin(struktural,
    #                        (PartnerDepartemen.jabatan_id == struktural.id)) \
    #             .order_by(Partner.nama)
    #         if self.req.user.company_id:
    #             q = q.filter(Departemen.company_id == self.req.user.company_id)
    #         row_table = DataTables(request.GET, q, columns)

    #         return row_table.output_result()

    #     elif url_dict['act'] == 'hon_departemen':
    #         term = 'term' in params and params['term'] or ''
    #         prefix = 'prefix' in params and params['prefix'] or ''
    #         q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
    #                                    PartnerDepartemen.jabatan_id,
    #                                    Jabatan.nama.label('jabatan_nm'),
    #                                    ). \
    #             join(PartnerDepartemen). \
    #             join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
    #             filter(Partner.nama.ilike('%%%s%%' % term)). \
    #             filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
    #             filter(or_(Jabatan.kode == '101', Jabatan.kode == '102')). \
    #             order_by(Partner.nama)
    #         if self.req.user.company_id:
    #             q = q.filter(Departemen.company_id == self.req.user.company_id)

    #         rows = q.all()
    #         r = []
    #         keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
    #         for k in rows:
    #             values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
    #             r.append(dict(zip(keys, values)))
    #         return r

    #     elif url_dict['act'] == 'hon_jabatan':
    #         term = 'term' in params and params['term'] or ''
    #         prefix = 'prefix' in params and params['prefix'] or ''
    #         partner_id = 'partner_id' in params and params['partner_id'] or 0
    #         # filter(or_(Jabatan.kode == '103', Jabatan.kode == '104')) dilepas sementara
    #         q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
    #                                    PartnerDepartemen.jabatan_id,
    #                                    Jabatan.nama.label('jabatan_nm'),
    #                                    ). \
    #             join(PartnerDepartemen). \
    #             join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
    #             filter(Partner.nama.ilike('%%%s%%' % term)). \
    #             filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
    #             order_by(Partner.nama)
    #         if self.req.user.company_id:
    #             q = q.filter(Departemen.company_id == self.req.user.company_id)
    #         rows = q.all()
    #         r = []
    #         keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
    #         for k in rows:
    #             values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
    #             r.append(dict(zip(keys, values)))
    #         return r

    #     elif url_dict['act'] == 'hon_skpkd':
    #         term = 'term' in params and params['term'] or ''
    #         prefix = 'prefix' in params and params['prefix'] or ''
    #         q = PartnerDBSession.query(Partner.id, Partner.nik, Partner.nama,
    #                                    PartnerDepartemen.jabatan_id,
    #                                    Jabatan.nama.label('jabatan_nm'),
    #                                    ). \
    #             join(PartnerDepartemen). \
    #             join(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)). \
    #             filter(Partner.nama.ilike('%%%s%%' % term)). \
    #             filter(PartnerDepartemen.departemen_id == ses['departemen_id']). \
    #             filter(or_(Jabatan.kode == '101', Jabatan.kode == '102',
    #                        Jabatan.kode == '103', Jabatan.kode ==
    #                        '104')). \
    #             order_by(Partner.nama)
    #         if self.req.user.company_id:
    #             q = q.filter(Departemen.company_id == self.req.user.company_id)
    #         rows = q.all()
    #         r = []
    #         keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
    #         for k in rows:
    #             values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
    #             r.append(dict(zip(keys, values)))
    #         return r

    #     elif url_dict['act'] == 'hon_jabatannm':
    #         term = 'term' in params and params['term'] or ''
    #         q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama,
    #                             Jabatan.jenis). \
    #             filter(Jabatan.nama.ilike('%%%s%%' % term)). \
    #             order_by(Jabatan.nama)
    #         if self.req.user.company_id:
    #             q = q.filter(Departemen.company_id == self.req.user.company_id)
    #         rows = q.all()
    #         r = []
    #         for k in rows:
    #             if k[3] == 1:
    #                 nama_jenis = 'Struktural'
    #             elif k[3] == 2:
    #                 nama_jenis = 'Fungsional'
    #             else:
    #                 nama_jenis = 'Keuangan'

    #             d = {}
    #             d['id'] = k[0]
    #             d['value'] = k[2] + ' (' + nama_jenis + ')'
    #             d['kode'] = k[1]
    #             d['nama'] = k[2]
    #             r.append(d)
    #         return r

    def next_act(self):
        act = self.req.matchdict['act']
        if act == 'partner':
            term = self.params.get('term', '')
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                order_by(Partner.nama)
            return [{"id":k[0], "value":k[1], "kode":k[2], "nama":k[3]} for k in q.all()]
        
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

    def before_add(self):
        values = {'departemen_id': self.ses.get('departemen_id', None),
                  'departemen_nm': self.ses.get('departemen_nm', ""),
                  'departemen_kd': self.ses.get('departemen_kd', "")}
        return values
