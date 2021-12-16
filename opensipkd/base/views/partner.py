# from ..tools import row2dict, xls_reader
from datetime import datetime

import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
)
from opensipkd.base.models import User, ResProvinsi, ResDati2, ResKecamatan, ResDesa
from pyramid.httpexceptions import (
    HTTPFound,
)
from pyramid.view import (
    view_config,
)
from opensipkd.tools.buttons import btn_save, btn_cancel, btn_delete

from .dati2 import dati2_widget
from .desa import desa_widget
from .kecamatan import kecamatan_widget
from .provinsi import provinsi_widget
from ..models import DBSession
from ..models import Partner
# from ..models.partner import PartnerUserModel
from ..views import ColumnDT, DataTables, BaseView

SESS_ADD_FAILED = 'Tambah partner gagal'
SESS_EDIT_FAILED = 'Edit partner gagal'


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode",
        title="Kode")
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama")
    alamat_1 = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=128),
        oid="alamat_1")
    alamat_2 = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        validator=colander.Length(max=128),
        oid="alamat_2")
    # kelurahan = colander.SchemaNode(
    #     colander.String(),
    #     missing=colander.drop,
    #     validator=colander.Length(max=64),
    #     oid="kelurahan")
    # kecamatan = colander.SchemaNode(
    #     colander.String(),
    #     missing=colander.drop,
    #     validator=colander.Length(max=64),
    #     oid="kecamatan")
    # kota = colander.SchemaNode(
    #     colander.String(),
    #     validator=colander.Length(max=64),
    #     missing=colander.drop,
    #     oid="kota")
    # provinsi = colander.SchemaNode(
    #     colander.String(),
    #     validator=colander.Length(max=64),
    #     missing=colander.drop,
    #     oid="provinsi")
    provinsi_id = colander.SchemaNode(
        colander.Integer(),
        widget=provinsi_widget,
        missing=colander.drop,
        oid="provinsi_id",
        url="",
        slave="dati2_id",
    )
    dati2_id = colander.SchemaNode(
        colander.Integer(),
        widget=dati2_widget,
        missing=colander.drop,
        oid="dati2_id")
    kecamatan_id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=kecamatan_widget,
        oid="kecamatan_id")
    desa_id = colander.SchemaNode(
        colander.Integer(),
        widget=desa_widget,
        missing=colander.drop,
        oid="desa_id")
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=128),
        oid="email")
    phone = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        missing=colander.drop,
        oid="phone")
    fax = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        missing=colander.drop,
        oid="fax")
    mobile = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=16),
        missing=colander.drop,
        oid="mobile")
    website = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=128),
        missing=colander.drop,
        oid="website")
    is_vendor = colander.SchemaNode(
        colander.Boolean(),
        oid="is_vendor",
        title="Vendor")
    is_customer = colander.SchemaNode(
        colander.Boolean(),
        oid="is_customer",
        title="Customer")
    status = colander.SchemaNode(
        colander.Boolean(),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ViewPartner(BaseView):
    ########
    # List #
    ########
    @view_config(route_name='partner', renderer='templates/partner/list.pt',
                 permission='user-view')
    def view_list(self):
        return dict()

    @view_config(route_name='partner-act', renderer='json',
                 permission='user-view')
    def view_act(self):
        request = self.req
        params = request.params
        url_dict = request.matchdict

        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(Partner.id, mData='id'),
                ColumnDT(Partner.kode, mData='kode'),
                ColumnDT(Partner.nama, mData='nama'),
                ColumnDT(Partner.is_vendor, mData='is_vendor'),
                ColumnDT(Partner.is_customer, mData='is_customer'),
                ColumnDT(Partner.status, mData='status'),
            ]
            query = DBSession.query().select_from(Partner)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()

        elif url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.kode.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_vendor == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                order_by(Partner.nama)
            row = q.first()
            if not row:
                return []

            keys = row.keys()
            r = [dict(zip(keys, k)) for k in q.all()]
            return r

        elif url_dict['act'] == 'vendor':  # vendor only
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_vendor == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

        elif url_dict['act'] == 'customer':  # customer only
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            q = DBSession.query(Partner.id, Partner.nama.label('value'),
                                Partner.kode, Partner.nama). \
                filter(Partner.nama.ilike('%%%s%%' % term)). \
                filter(Partner.is_customer == 1). \
                order_by(Partner.nama)
            keys = q.first().keys()
            r = []
            for k in q.all():
                d = dict(zip(keys, k))
                r.append(d)
            return r

    @view_config(route_name='partner-add', renderer='templates/form_input.pt',
                 permission='user-edit')
    def view_add(self):
        request = self.req
        form = get_form(request, AddSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), scripts="")
                save_request(request, dict(controls))
            return route_list(request)
        return dict(form=form.render(), scripts="")

    @view_config(route_name='partner-edt', renderer='templates/form_input.pt',
                 permission='user-edit')
    def view_edt(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema, row=row)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form.render(), scripts="")

                save_request(request, dict(controls), row)
            return route_list(request)

        values = row.to_dict()
        form.render(appstruct=values)
        return dict(form=form.render(), scripts="")

    @view_config(route_name='partner-view', renderer='templates/form_input.pt',
                 permission='user-edit')
    def view_view(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema, buttons=(btn_cancel,))
        if request.POST:
            return route_list(request)

        values = row.to_dict()
        form.render(appstruct=values)
        return dict(form=form.render(readonly=True), scripts="")

    @view_config(route_name='partner-del', renderer='templates/form_input.pt',
                 permission='user-edit')
    def view_del(self):
        request = self.req
        q = query_id(request)
        row = q.first()
        if not row:
            return id_not_found(request)

        form = get_form(request, EditSchema, buttons=(btn_delete, btn_cancel,))
        if request.POST:
            if 'delete' in request.POST:
                user = User.query(). \
                    filter_by(partner_id=request.matchdict['id'])
                if user.first():
                    request.session.flash('Partner digunakan oleh User')
                    return route_list(request)
                msg = 'Partner ID %d %s sudah dihapus.' % (row.id, row.nama)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return route_list(request)

        values = row.to_dict()
        form.render(appstruct=values)
        return dict(form=form.render(readonly=True), scripts="")


def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
                               'Kode %s sudah digunakan oleh %s' % (
                                   value['kode'], found.nama))

    # def err_login():
    # raise colander.Invalid(form,
    # 'Login %s sudah digunakan oleh kode %s' % (
    # value['user_nm'], found.row.nama))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Partner).filter_by(id=uid)
        row = q.first()
    else:
        row = None
    q = Partner.query_kode(value['kode'])
    found = q.first()
    if row:
        if found and found.id != row.id:
            err_kode()
    elif found:
        err_kode()


def get_form(request, class_form, row=None, buttons=(btn_save, btn_cancel)):
    schema = class_form(validator=form_validator)
    provinsi_list = ResProvinsi.get_list()
    dati2_list = row and row.provinsi_id and ResDati2.get_list(row.provinsi_id) or []
    kecamatan_list = row and row.dati2_id and ResKecamatan.get_list(row.dati2_id) or []
    desa_list = row and row.kecamatan_id and ResDesa.get_list(row.kecamatan_id) or []
    schema = schema.bind(provinsi_list=provinsi_list,
                         dati2_list=dati2_list,
                         kecamatan_list=kecamatan_list,
                         desa_list=desa_list
                         )
    schema.request = request
    # if row:
    #     schema.deserialize(row)
    return Form(schema, buttons=buttons)


def save(values, user, row=None):
    if not row:
        row = Partner()
        row.created = datetime.now()
        row.create_uid = user.id
    values['is_vendor'] = 'is_vendor' in values and values['is_vendor'] and 1 or 0
    values['is_customer'] = 'is_customer' in values and values['is_customer'] and 1 or 0
    row.from_dict(values)
    row.updated = datetime.now()
    row.update_uid = user.id
    row.status = 'status' in values and values['status'] and 1 or row and row.status or 0
    DBSession.add(row)
    DBSession.flush()
    return row


def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Partner sudah disimpan.')


def route_list(request):
    return HTTPFound(location=request.route_url('partner'))


def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r


########
# Edit #
########
def query_id(request):
    return DBSession.query(Partner).filter_by(id=request.matchdict['id'])


def id_not_found(request):
    msg = 'Partner ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)


def get_partner_list():
    r = []
    q = DBSession.query(Partner).order_by(Partner.nama)
    for row in q:
        g = (str(row.id), (f"{row.kode}/ {row.nama}"))
        r.append(g)
    return r


@colander.deferred
def partner_widget(node, kw):
    values = kw.get('partner_list', [])
    return widget.Select2Widget(values=values)
