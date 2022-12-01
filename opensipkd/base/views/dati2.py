import colander
from deform import (widget, )
from pyramid.i18n import TranslationStringFactory
from pyramid.view import (view_config, )

from . import widget_os
from .provinsi import provinsi_widget
from opensipkd.models import DBSession, ResDati2, kategori_dati2, ResProvinsi
from ..views import BaseView

_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah dati2 gagal'
SESS_EDIT_FAILED = 'Edit dati2 gagal'


@colander.deferred
def dati2_widget(node, kw):
    values = kw.get('dati2_list', [])
    url = node and hasattr(node, 'slave_url') and node.slave_url or ""
    slave = node and hasattr(node, 'slave') and node.slave or ""
    values.insert(0, ("", "Pilih Kab/Kota..."))
    return widget_os.Select2MsWidget(values=values,
                                     url=url,
                                     slave=slave,
                                     placeholder="Pilih Kota/Kabupaten"
                                     )


class AddSchema(colander.Schema):
    provinsi_id = colander.SchemaNode(colander.String(),
                                      widget=provinsi_widget,
                                      validator=colander.Length(max=32),
                                      oid="kode")
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    kategori = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(
                                       values=kategori_dati2),
                                   validator=colander.Length(max=32),
                                   oid="kode")

    nama = colander.SchemaNode(colander.String(), oid="nama")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(),
                             title=_("action", default="Action"))
    kode = colander.SchemaNode(colander.String(), width='100pt', title="Kode")
    nama = colander.SchemaNode(colander.String(), title="Nama")
    provinsi = colander.SchemaNode(colander.String(), field=ResProvinsi.nama)


class ViewDati2(BaseView):
    def __init__(self, request):
        super(ViewDati2, self).__init__(request)
        self.form_scripts = ""
        self.form_params = dict(scripts="")
        self.list_url = 'dati2'
        self.list_route = 'dati2'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResDati2
        self.list_schema = ListSchema

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
            q = DBSession.query(ResDati2).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResDati2.query_kode(value['kode']) \
            .filter(ResDati2.provinsi_id == value["provinsi_id"])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResDati2.query_nama(value['nama']) \
            .filter(ResDati2.provinsi_id == value["provinsi_id"]).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    def get_bindings(self, row=None):
        return dict(provinsi_list=ResProvinsi.get_list())

    @view_config(route_name='dati2',
                 renderer='templates/table.pt',
                 permission='wilayah')
    def view_list(self):
        return super(ViewDati2, self).view_list()

    @view_config(route_name='dati2-view',
                 renderer='templates/form.pt', permission='wilayah')
    def view_view(self):  # row = query_id(request).first()
        return super(ViewDati2, self).view_view()

    def list_join(self, query):
        return query.join(ResProvinsi, ResProvinsi.id == ResDati2.provinsi_id)

    @view_config(route_name='dati2-act', renderer='json',
                 permission='view')
    def view_act(self):
        return super().view_act()

    def next_act(self):
        url_dict = self.req.matchdict
        if url_dict['act'] == 'select':
            provinsi_id = self.req.params["provinsi_id"]
            data = ResDati2.get_list(provinsi_id)
            result = {f"{k[0]}": k[1] for k in data}
            return result

    @view_config(route_name='dati2-add',
                 renderer='templates/form.pt', permission='wilayah')
    def view_add(self):
        return super(ViewDati2, self).view_add()

    @view_config(route_name='dati2-edit',
                 renderer='templates/form.pt', permission='wilayah')
    def view_edt(self):
        return super(ViewDati2, self).view_edit()

    @view_config(route_name='dati2-delete',
                 renderer='templates/form.pt', permission='wilayah')
    def view_delete(self):
        return super(ViewDati2, self).view_delete()

    @view_config(route_name='dati2-upload',
                 renderer='templates/form.pt', permission='wilayah')
    def view_upload(self):
        return super(ViewDati2, self).view_upload(exts=(".csv",))
