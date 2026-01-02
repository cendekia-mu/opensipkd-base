import colander
from deform import (widget, )
from opensipkd.base.views.provinsi import provinsi_widget
from opensipkd.models import DBSession, ResKecamatan, ResDati2, ResProvinsi
from opensipkd.tools.buttons import btn_upload, btn_add, btn_delete
from pyramid.i18n import TranslationStringFactory
from ..widgets import widget_os
from .dati2 import dati2_widget
from ..views import BaseView
SESS_ADD_FAILED = 'Tambah kecamatan gagal'
SESS_EDIT_FAILED = 'Edit kecamatan gagal'
_ = TranslationStringFactory("opensipkd")


@colander.deferred
def kecamatan_widget(node, kw):
    values = kw.get('kecamatan_list', [])
    url = node and hasattr(node, 'slave_url') and node.slave_url or ""
    slave = node and hasattr(node, 'slave') and node.slave or ""
    values.insert(0, ("", "Pilih Kecamatan..."))
    return widget_os.Select2MsWidget(values=values,
                                     url=url,
                                     slave=slave,
                                     placeholder="Pilih Kecamatan")


class AddSchema(colander.Schema):
    provinsi_id = colander.SchemaNode(
        colander.String(),
        widget=provinsi_widget,
        validator=colander.Length(max=32),
        oid="provinsi_id",
        slave="dati2_id",
        slave_url="/dati2/select/act?provinsi_id=",
        title="Provinsi",
    )
    dati2_id = colander.SchemaNode(
        colander.String(),
        widget=dati2_widget,
        validator=colander.Length(max=32),
        oid="dati2_id")
    kode = colander.SchemaNode(
        colander.String(),
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
    kabupaten = colander.SchemaNode(colander.String(), field=ResDati2.nama)


class Views(BaseView):
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.form_params = dict(scripts="")
        self.list_route = 'base-kecamatan'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResKecamatan
        self.list_schema = ListSchema
        self.list_buttons = [btn_add, btn_delete, btn_upload]
        self.allow_check = True
        self.allow_view = True
        self.allow_delete = True
        self.list_view_field = 'nama'
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



    def next_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'select':
            dati2_id = request.params["dati2_id"]
            data = ResKecamatan.get_list(dati2_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result

    def get_bindings(self, row=None):
        provinsi_list = ResProvinsi.get_list()
        kecamatan = row
        dati2 = kecamatan and kecamatan.dati2 or None
        dati2_list = dati2 and ResDati2.get_list(dati2.provinsi_id) or []
        return dict(
            provinsi_list=provinsi_list,
            dati2_list=dati2_list,
        )

    def get_values(self, row, istime=False):
        d = super().get_values(row, istime)
        kecamatan = row
        dati2 = kecamatan and kecamatan.dati2 or None
        d["provinsi_id"] = dati2 and dati2.provinsi_id or None
        return d
    
    def list_join(self, query):
        return query.join(ResDati2, ResDati2.id == ResKecamatan.dati2_id)

    # @view_config(route_name='kecamatan-upload',
    #              renderer='templates/form.pt', permission='wilayah')
    def view_upload(self):
        return super().view_upload(exts=(".csv", ".tsv"))


    #     @view_config(route_name='kecamatan-view',
    #                  renderer='templates/form.pt', permission='wilayah')
    # def view_view(self):  # row = query_id(request).first()
    #     return super().view_view()

    # @view_config(route_name='kecamatan',
    #              renderer='templates/table.pt',
    #              permission='wilayah')
    # def view_list(self):
    #     return super(Views, self).view_list()

    # @view_config(route_name='kecamatan-act', renderer='json',
    #              permission='view')
    # def view_act(self):
    #     return super().view_act()

     # @view_config(route_name='kecamatan-add',
    #              renderer='templates/form.pt', permission='wilayah')
    # def view_add(self):
    #     return super(Views, self).view_add()
    # @view_config(route_name='kecamatan-edit',
    #              renderer='templates/form.pt', permission='wilayah')
    # def view_edt(self):
    #     return super(Views, self).view_edit()

    # @view_config(route_name='kecamatan-delete',
    #              renderer='templates/form.pt', permission='wilayah')
    # def view_delete(self):
    #     return super(Views, self).view_delete()


