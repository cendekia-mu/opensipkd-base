import colander
import json
from deform import (Form, widget, ValidationFailure, )
from pyramid.httpexceptions import (HTTPFound, )
from pyramid.view import (view_config, )
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from ..models import DBSession as PartnerDBSession, DBSession
from ..models import Departemen, Jabatan
from ..models import Partner, PartnerDepartemen
from opensipkd.tools import dmy, date_from_str
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_delete, btn_close
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
        oid="mulai",
        widget=widget.TextInputWidget(css_class="date"))
    selesai = colander.SchemaNode(
        colander.String(),
        oid="selesai",
        widget=widget.TextInputWidget(css_class="date"))


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())

class ViewPartner(BaseView):
    def __init__(self, request):
        super(ViewPartner, self).__init__(request)
        self.form_scripts = """
        $(document).ready(function () {

            $('#pegawai_nm').typeahead({
                "hint"     : true,
                "highlight": true,
                "minLength": 1,
                "remote"   : {
                        url: "/partner/hon/act?term=%QUERY",
                        beforeSend: function () {
                            $('#partner_nm').addClass("loading");
                        },
                        filter: function(parsedResponse){
                            $('#partner_nm').removeClass('loading');
                            return parsedResponse;
                        }
                },
            },{
                "name"      : 'partner_nm',
                "displayKey": 'value',
            });

            $('#partner_nm').bind('typeahead:selected', function(obj, datum, name) {
              $('#partner_id').val(datum.id);
              $('#partner_nm').val(datum.nama);
            });

            $('#departemen_nm').typeahead({
                "hint"     : true,
                "highlight": true,
                "minLength": 1,
                "remote"   : {
                        url: "/departemen/hon/act?term=%QUERY",
                        beforeSend: function () {
                            $('#departemen_nm').addClass("loading");
                        },
                        filter: function(parsedResponse){
                            $('#departemen_nm').removeClass('loading');
                            return parsedResponse;
                        }
                },
            },{
                "name"      : 'departemen_nm',
                "displayKey": 'value',
            });

            $('#departemen_nm').bind('typeahead:selected', function(obj, datum, name) {
              $('#departemen_id').val(datum.id);
            });



            $('#jabatan_nm').typeahead({
                "hint"     : true,
                "highlight": true,
                "minLength": 1,
                "remote"   : {
                        url: "/partner/departemen/hon_jabatannm/act?term=%QUERY",
                        beforeSend: function () {
                            $('#jabatan_nm').addClass("loading");
                        },
                        filter: function(parsedResponse){
                            $('#jabatan_nm').removeClass('loading');
                            return parsedResponse;
                        }
                },
            },{
                "name"      : 'jabatan_nm',
                "displayKey": 'value',
            });

            $('#jabatan_nm').bind('typeahead:selected', function(obj, datum, name) {
              $('#jabatan_id').val(datum.id);
              $('#jabatan_nm').val(datum.value);
              
            });
        });
        """

        self.list_col_defs = json.dumps(
            [{"searchable": False, "visible": False, "targets": [0], }, {
                "searchable": True, "orderable": True, "targets": [1, 2],
            }])
        self.list_cols = [{'title': "ID", 'data': "id"},
                          {'title': "NIP", 'data': "nik", 'width': '100pt'},
                          {'title': "Nama", 'data': "nama"}, 
                          {'title': "Unit Kerja", 'data': "departemen"},
                          {'title': "Jabatan", 'data': "jabatan"},
                          {'title': "Jenis Jabatan", 'data': "jenis"},
                          {'title': "Mulai", 'data': "mulai"},
                          {'title': "Selesai", 'data': "selesai"},]
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        self.list_url = 'partner/departemen'
        self.list_route = 'partner-departemen'

    @staticmethod
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

            
    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel)):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(request=self.req)
        schema.request = self.req
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons)

    def save(self, values, user, row=None):
        if not row:
            row = PartnerDepartemen()
        row.from_dict(values)
        PartnerDBSession.add(row)
        PartnerDBSession.flush()
        return row


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
        query_struktural = DBSession.query(Jabatan.jenis).\
            filter(Jabatan.id == values['jabatan_id']).scalar()
        values['struktural_id'] = query_struktural
        row = self.save(values, request.user, row)
        request.session.flash('Posisi Partner sudah disimpan.')


    def route_list(self, ):
        return HTTPFound(location=self.req.route_url(self.list_route))


    def session_failed(self, session_name):
        r = dict(form=self.request.session[session_name])
        del self.request.session[session_name]
        return r


    def query_id(self):
        return PartnerDBSession.query(PartnerDepartemen).filter_by(id=self.req.matchdict['id'])


    def id_not_found(self):
        msg = 'Posisi Partner ID %s Tidak Ditemukan.' % self.req.matchdict['id']
        self.request.session.flash(msg, 'error')
        return route_list()


    ########
    # List #
    ########    
    @view_config(route_name='partner-departemen', renderer='templates/list.pt',
                 permission='view')
    def view_list(self):
        return super().view_list()

    ##########
    # Action #
    ##########    
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

    @view_config(route_name='partner-departemen-view',
                 renderer='templates/form_input.pt', permission='partner-departemen')
    def view_view(self):  # row = query_id(request).first()
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()

        form = self.get_form(EditSchema, buttons=(btn_close,))
        if request.POST:
            return self.route_list()

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

        form.set_appstruct(self.get_values(row, values))
        return dict(form=form.render(readonly=True), scripts=self.form_scripts)


    #########
    #  Add  #
    #########       
    @view_config(route_name='partner-departemen-add', renderer='templates/form_input.pt',
                 permission='partner-departemen')
    def view_add(self):
        request = self.req
        form = self.get_form(AddSchema)
        values = {}
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct = e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)
                self.save_request(dict(controls))
            return self.route_list()
        values['departemen_id'] = self.ses['departemen_id']
        values['departemen_nm'] = self.ses['departemen_nm']
        values['departemen_kd'] = self.ses['departemen_kd']
        form.set_appstruct(values)
        return dict(form=form.render(), scripts=self.form_scripts)

    ##########
    #  Edit  #
    ##########
    @view_config(route_name='partner-departemen-edit', renderer='templates/form_input.pt',
                 permission='partner-departemen')
    def view_edt(self):
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()

        form = self.get_form(EditSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)

                self.save_request(dict(controls), row)
            return self.route_list()

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

        form.set_appstruct(self.get_values(row, values))
        return dict(form=form.render(), scripts=self.form_scripts)

    ##########
    # Delete #
    ##########
    @view_config(route_name='partner-departemen-delete', renderer='templates/form_input.pt',
                 permission='partner-departemen')
    def view_del(self):
        request = self.req
        q = self.query_id()
        row = q.first()

        if not row:
            return self.id_not_found()

        if request.POST:
            if 'delete' in request.POST:
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
            return self.route_list()
        form = self.get_form(EditSchema,
                             buttons=(btn_delete, btn_cancel))
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
        form.set_appstruct(self.get_values(row, values))
        return dict(row=row,form=form.render(readonly=True), scripts=self.form_scripts)

    def get_values(self, row, values=None):
        if not values:
            values = row.to_dict()

        return values