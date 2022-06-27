import colander
from deform import (widget, )
from pyramid.view import (view_config, )

from ..models import Permission
from ..views import BaseView

SESS_ADD_FAILED = 'Tambah permission gagal'
SESS_EDIT_FAILED = 'Edit permission gagal'


class AddSchema(colander.Schema):
    perm_name = colander.SchemaNode(
        colander.String(),
        oid="perm_name",
        title="Nama")
    description = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        oid="description",
        title="Diskripsi")


class EditSchema(AddSchema):
    id = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        widget=widget.HiddenWidget(),
        visible=False
    )


class ViewPermission(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'permission'
        self.list_route = 'permission'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Permission
        self.list_schema = EditSchema

    @view_config(route_name='permission', renderer='templates/table.pt',
                 permission='user-edit')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='permission-act', renderer='json',
                 permission='user-edit')
    def view_act(self):
        return super().view_act()

    @view_config(route_name='permission-add', renderer='templates/form.pt',
                 permission='user-edit')
    def view_add(self):
        return super().view_add()

    @view_config(route_name='permission-edit', renderer='templates/form.pt',
                 permission='user-edit')
    def view_edt(self):
        return super().view_edit()

    @view_config(route_name='permission-delete', renderer='templates/form.pt',
                 permission='user-edit')
    def view_delete(self):
        return super().view_delete()
