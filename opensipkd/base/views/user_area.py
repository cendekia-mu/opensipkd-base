import colander
from deform import widget
from pyramid.view import view_config

from . import BaseView
from ..models import ResDesa, User, UserArea


class ListSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(),
        title="Action"
    )
    user_name = colander.SchemaNode(
        colander.String(),
        field=User.user_name,
        title="User"
    )
    desa_kd = colander.SchemaNode(
        colander.String(),
        field=ResDesa.kode)
    desa_name = colander.SchemaNode(
        colander.String(),
        field=ResDesa.nama)


class AddSchema(colander.Schema):
    user_id = colander.SchemaNode(
        colander.Integer(),
        # widget=widget.SelectWidget(values=User.get_list()),
        oid="user_id",
        title="User",
    )
    desa_id = colander.SchemaNode(
        colander.Integer(),
        # widget=widget.SelectWidget(values=ResDesa.get_list()),
        oid="desa_id",
        title="Kelurahan/Desa", )


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.list_route = 'user-area'
        self.table = UserArea

    def list_join(self, query, **kwargs):
        return query.outerjoin(ResDesa, ResDesa.id == self.table.desa_id) \
            .outerjoin(User, User.id == self.table.user_id)

    # @view_config(route_name='user-area', renderer='templates/table.pt',
    #              permission='user-view')
    # def view_list(self, **kwargs):
    #     return super().view_list(**kwargs)

    # @view_config(route_name='user-area-act', renderer='json',
    #              permission='user-view')
    # def view_act(self):
    #     return super().view_act()

    # @view_config(route_name='user-area-add', renderer='templates/form.pt',
    #              permission='user-edit')
    # def view_add(self):
    #     return super().view_add()

    # @view_config(route_name='user-area-view', renderer='templates/form.pt',
    #              permission='user-view')
    # def view_view(self):
    #     return super().view_view()

    # @view_config(route_name='user-area-delete', renderer='templates/form.pt',
    #              permission='user-edit')
    # def view_delete(self):
    #     return super().view_delete()

    # @view_config(route_name='user-area-edit', renderer='templates/form.pt',
    #              permission='user-edit')
    # def view_edit(self):
    #     return super().view_edit()
