import colander
from deform import (widget, )
from opensipkd.tools.buttons import btn_upload, btn_close, btn_add
from pyramid.i18n import TranslationStringFactory
from pyramid.view import (view_config, )

from .dati2 import dati2_widget
from .kecamatan import kecamatan_widget
from .provinsi import provinsi_widget
from opensipkd.models import DBSession, ResDesa, kategori_desa, ResKecamatan, ResProvinsi, ResDati2
from ..views import BaseView
_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah desa gagal'
SESS_EDIT_FAILED = 'Edit desa gagal'


@colander.deferred
def desa_widget(node, kw):
    values = kw.get('desa_list', [])
    return widget.Select2Widget(values=values,
                                placeholder="Pilih Desa/Kelurahan")


class AddSchema(colander.Schema):
    provinsi_id = colander.SchemaNode(colander.String(),
                                      widget=provinsi_widget,
                                      validator=colander.Length(max=32),
                                      oid="provinsi_id",
                                      slave="dati2_id",
                                      slave_url="/dati2/select/act?provinsi_id=",
                                      title="Provinsi",
                                      )
    dati2_id = colander.SchemaNode(colander.String(),
                                   widget=dati2_widget,
                                   validator=colander.Length(max=32),
                                   oid="dati2_id",
                                   slave="kecamatan_id",
                                   slave_url="/kecamatan/select/act?dati2_id=",
                                   title="Kabupaten/Kota",
                                   )
    kecamatan_id = colander.SchemaNode(colander.String(),
                                       widget=kecamatan_widget,
                                       validator=colander.Length(max=32),
                                       oid="kecamatan_id",
                                       title="Kecamatan")
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    kategori = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=kategori_desa),
                                   validator=colander.Length(max=32), oid="kode")

    nama = colander.SchemaNode(colander.String(), oid="nama")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(),
                             title=_("action", default="Action"))
    kode = colander.SchemaNode(colander.String(), width='100pt', title="Kode")
    nama = colander.SchemaNode(colander.String(), title="Nama")
    kecamatan = colander.SchemaNode(colander.String(), field=ResKecamatan.nama)


class ViewDesa(BaseView):
    def __init__(self, request):
        super(ViewDesa, self).__init__(request)
        self.form_scripts = ""
        self.form_params = dict(scripts="")
        self.list_url = 'desa'
        self.list_route = 'desa'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResDesa
        self.list_schema = ListSchema
        self.list_buttons = (btn_add, btn_close, btn_upload)

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

    def get_bindings(self, row=None):
        provinsi_list = ResProvinsi.get_list()
        kecamatan = row and row.kecamatan or None
        kecamatan_list = kecamatan and ResKecamatan.get_list(kecamatan.dati2_id) or []
        dati2 = kecamatan and kecamatan.dati2 or None
        dati2_list = dati2 and ResDati2.get_list(dati2.provinsi_id) or []
        return dict(
            provinsi_list=provinsi_list,
            dati2_list=dati2_list,
            kecamatan_list=kecamatan_list,
        )

    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        kecamatan = row and row.kecamatan or None
        d["dati2_id"] = kecamatan and kecamatan.dati2_id or None
        dati2 = kecamatan and kecamatan.dati2 or None
        d["provinsi_id"] = dati2 and dati2.provinsi_id or None
        return d

    @view_config(route_name='desa-view',
                 renderer='templates/form.pt', permission='desa')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='desa',
                 renderer='templates/table.pt',
                 permission='desa')
    def view_list(self):
        return super(ViewDesa, self).view_list()

    def list_join(self, query):
        return query.outerjoin(ResKecamatan)

    @view_config(route_name='desa-act', renderer='json',
                 permission='view')
    def view_act(self):
        return super().view_act()

    def next_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'select':
            kecamatan_id = request.params["kecamatan_id"]
            data = ResDesa.get_list(kecamatan_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result

    @view_config(route_name='desa-add',
                 renderer='templates/form.pt', permission='desa')
    def view_add(self):
        return super(ViewDesa, self).view_add()

    @view_config(route_name='desa-edit',
                 renderer='templates/form.pt', permission='desa')
    def view_edt(self):
        return super(ViewDesa, self).view_edit()

    @view_config(route_name='desa-delete',
                 renderer='templates/form.pt', permission='desa')
    def view_delete(self):
        return super(ViewDesa, self).view_delete()

    @view_config(route_name='desa-upload',
                 renderer='templates/form.pt', permission='desa')
    def view_upload(self):
        return super(ViewDesa, self).view_upload(exts=('.csv',))
