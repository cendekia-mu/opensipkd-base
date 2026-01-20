import colander
from deform import widget
from opensipkd.base.models import Pangkat
from opensipkd.base.views import base_views


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="Action")
    kode = colander.SchemaNode(
        colander.String(),)
    nama = colander.SchemaNode(
        colander.String(),)
    pangkat = colander.SchemaNode(
        colander.String(),)
    ruang = colander.SchemaNode(
        colander.String(),)
    status = colander.SchemaNode(
        colander.Integer(), widget=widget.CheckboxWidget(),)


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode")
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    pangkat = colander.SchemaNode(
        colander.String(),
        oid="pangkat")
    ruang = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=1),
        oid="ruang")
    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class Views(base_views.BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_route = 'base-pangkat'
        self.table = Pangkat
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
