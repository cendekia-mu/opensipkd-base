import colander
from deform import (Form, widget, ValidationFailure, )
from pyramid.httpexceptions import (HTTPFound, )
from pyramid.view import (view_config, )
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from ..models import DBSession as PartnerDBSession, DBSession
from ..models import Departemen, Jabatan
from ..models import Partner, PartnerDepartemen
from opensipkd.tools import dmy, date_from_str
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah posisi partner gagal'
SESS_EDIT_FAILED = 'Edit posisi partner gagal'


class AddSchema(colander.Schema):
    departemen_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/departemen/hon/act',
        min_length=1)

    nama_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/partner/hon/act',
        min_length=1)

    jabatan_widget = widget.AutocompleteInputWidget(
        size=60,
        values='/jabatan/hon/act',
        min_length=1)

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
        oid="mulai")
    selesai = colander.SchemaNode(
        colander.String(),
        oid="selesai")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class ViewPartner(BaseView):
    ########
    # List #
    ########    
    @view_config(route_name='partner-departemen', renderer='templates/posisi/list.pt',
                 permission='partner-departemen')
    def view_list(self):
        return dict(a={})

    ##########
    # Action #
    ##########    
    @view_config(route_name='partner-departemen-act', renderer='json',
                 permission='read')
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
                ColumnDT(Jabatan.jenis, mData='jenis'),
                ColumnDT(struktural.nama, mData='struktural_nm'),
                ColumnDT(PartnerDepartemen.mulai, mData='mulai'),
                ColumnDT(PartnerDepartemen.selesai, mData='selesai'),
            ]
            query = PartnerDBSession.query().select_from(PartnerDepartemen) \
                .outerjoin(Departemen, PartnerDepartemen.departemen_id == Departemen.id) \
                .outerjoin(Partner, Partner.id == PartnerDepartemen.partner_id) \
                .outerjoin(Jabatan, (PartnerDepartemen.jabatan_id == Jabatan.id)) \
                .outerjoin(struktural, (PartnerDepartemen.struktural_id == struktural.id)) \
                .order_by(Partner.nama)

            row_table = DataTables(request.GET, query, columns)
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
                filter(or_(Jabatan.kode == '101', Jabatan.kode == '102', Jabatan.kode == '103', Jabatan.kode ==
                           '104')). \
                order_by(Partner.nama)
            rows = q.all()
            r = []
            keys = ('id', 'value', 'nik', 'nama', 'jabatan_id', 'jabatan_nm')
            for k in rows:
                values = (k[0], k[2] + (" - ") + k[4], k[1], k[2], k[3], k[4])
                r.append(dict(zip(keys, values)))
            return r

        elif url_dict['act'] == 'hon_jabatannm':
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

    #########
    #  Add  #
    #########       
    @view_config(route_name='partner-departemen-add', renderer='templates/posisi/add.pt',
                 permission='partner-departemen-add')
    def view_add(self):
        request = self.req
        form = get_form(request, AddSchema)
        values = {}
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    # form.render(appstruct = e.cstruct)
                    return dict(form=form)
                save_request(request, dict(controls))
            return route_list(request)
        elif SESS_ADD_FAILED in request.session:
            return session_failed(request, SESS_ADD_FAILED)
        values['departemen_id'] = self.ses['departemen_id']
        values['departemen_nm'] = self.ses['departemen_nm']
        values['departemen_kd'] = self.ses['departemen_kd']
        # values['jabatan_id'] = self.ses['jabatan']
        # values['partner_id'] = self.ses['partner_id']
        form.set_appstruct(values)
        return dict(form=form)
        # return dict(form=form.render())

    ##########
    #  Edit  #
    ##########
    @view_config(route_name='partner-departemen-edit', renderer='templates/posisi/edt.pt',
                 permission='partner-departemen')
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
        values['nama'] = row.partner.nama
        values['jabatan'] = row.jabatan.nama
        values['departemen'] = row.departemen.nama
        values['mulai'] = dmy(row.mulai)
        values['selesai'] = dmy(row.selesai)
        if not row.struktural_id:
            values['struktural_id'] = 0
        else:
            jb = Jabatan.query_id(row.struktural_id).first()
            if jb:
                values['struktural_nm'] = jb.nama

        form.render(appstruct=values)
        return dict(form=form)

    ##########
    # Delete #
    ##########
    @view_config(route_name='partner-departemen-delete', renderer='templates/posisi/del.pt',
                 permission='partner-departemen-delete')
    def view_del(self):
        request = self.req
        q = query_id(request)
        row = q.first()

        if not row:
            return id_not_found(request)

        form = Form(colander.Schema(), buttons=('hapus', 'batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Posisi Partner ID %d %s sudah dihapus.' % (row.id, row.partner.nama)
                # qry_login = PartnerLogin.query_partner(request.params['id'])
                # if qry_login.first():
                # try:
                # qry_login.delete()
                # except:
                # self.session.flash('Gagal Hapus')
                # return dict(row=row, form=form.render())
                q.delete()
                PartnerDBSession.flush()
                request.session.flash(msg)
            return route_list(request)
        return dict(row=row, form=form.render())


def form_validator(form, value):
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


def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
        schema.deserialize(row)
    return Form(schema, buttons=('simpan', 'batal'))


def save(values, request, row=None):
    if not row:
        row = PartnerDepartemen()
    row.from_dict(values)
    PartnerDBSession.add(row)
    PartnerDBSession.flush()
    return row

    # if not row:
    #     row = Produk()
    # row.from_dict(values)
    # DBSession.add(row)
    # DBSession.flush()
    # return row


def save_request(request, values, row=None):
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
    query_struktural = DBSession.query(Jabatan.jenis).\
        filter(Jabatan.id == values['jabatan_id']).scalar()
    values['struktural_id'] = query_struktural
    row = save(values, request, row)
    request.session.flash('Posisi Partner sudah disimpan.')


def route_list(request):
    return HTTPFound(location=request.route_url('partner-departemen'))


def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r


def query_id(request):
    return PartnerDBSession.query(PartnerDepartemen).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'Posisi Partner ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
