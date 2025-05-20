import colander
from deform import (widget, )
from pyramid.view import (view_config, )

from opensipkd.models import Permission
from ..views import BaseView

SESS_ADD_FAILED = 'Tambah permission gagal'
SESS_EDIT_FAILED = 'Edit permission gagal'

class ListSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        widget=widget.HiddenWidget(),
        visible=False,
        title="ACT")
    perm_name = colander.SchemaNode(
        colander.String(),
        oid="perm_name",
        title="Nama")
    description = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        oid="description",
        title="Diskripsi")
    
class EditSchema(ListSchema):
    pass

class AddSchema(EditSchema):
    def after_bind(self, schema, kwargs):
        del schema['id']

class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_route = 'base-permission'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Permission
        self.list_schema = EditSchema
