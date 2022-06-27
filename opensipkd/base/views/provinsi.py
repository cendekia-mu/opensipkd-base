import colander
from deform import (widget, )
from pyramid.view import (view_config, )

from . import widget_os
from ..models import DBSession, ResProvinsi, kategori_provinsi
from ..views import BaseView

SESS_ADD_FAILED = 'Tambah provinsi gagal'
SESS_EDIT_FAILED = 'Edit provinsi gagal'


@colander.deferred
def provinsi_widget(node, kw):
    values = kw.get('provinsi_list', [])
    url = node and hasattr(node, 'slave_url') and node.slave_url or ""
    slave = node and hasattr(node, 'slave') and node.slave or ""
    values.insert(0, ("", "Pilih Propinsi..."))
    return widget_os.Select2MsWidget(values=values,
                                     url=url,
                                     slave=slave,
                                     placeholder="Pilih Provinsi")


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(colander.String(),
                               oid="kode",
                               validator=colander.Length(max=32), )
    kategori = colander.SchemaNode(colander.String(),
                                   widget=widget.SelectWidget(values=kategori_provinsi),
                                   validator=colander.Length(max=32), oid="kode")

    nama = colander.SchemaNode(colander.String(), oid="nama")
    ibu_kota = colander.SchemaNode(colander.String(), oid="nama", missing=colander.drop)


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True),
                             visible=False)


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), searchable=False, orderable=False, visible=False)
    kode = colander.SchemaNode(colander.String(), width=100)
    nama = colander.SchemaNode(colander.String())
    ibu_kota=colander.SchemaNode(colander.String())


class ViewProvinsi(BaseView):
    def __init__(self, request):
        super(ViewProvinsi, self).__init__(request)
        self.form_scripts = ""
        self.form_params = dict(scripts="")
        self.list_route = 'provinsi'
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = ResProvinsi

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
            q = DBSession.query(ResProvinsi).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        q = ResProvinsi.query_kode(value['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

        found = ResProvinsi.query_nama(value['nama']).first()
        if found:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

    @view_config(route_name='provinsi-view',
                 renderer='templates/form.pt', permission='provinsi')
    def view_view(self):  # row = query_id(request).first()
        return super(ViewProvinsi, self).view_view()

    @view_config(route_name='provinsi',
                 renderer='templates/table.pt',
                 permission='provinsi')
    def view_list(self):
        return super(ViewProvinsi, self).view_list()

    @view_config(route_name='provinsi-act', renderer='json',
                 permission='view')
    def view_act(self):
        return super(ViewProvinsi, self).view_act()

    @view_config(route_name='provinsi-add',
                 renderer='templates/form.pt', permission='provinsi')
    def view_add(self):
        return super(ViewProvinsi, self).view_add()

    @view_config(route_name='provinsi-edit',
                 renderer='templates/form.pt', permission='provinsi')
    def view_edt(self):
        return super(ViewProvinsi, self).view_edit()

    @view_config(route_name='provinsi-delete',
                 renderer='templates/form.pt', permission='provinsi')
    def view_delete(self):
        return super(ViewProvinsi, self).view_delete()
