import colander
from deform import widget
from pyramid.view import view_config

from . import BaseView
from ...models import User, DepartemenUser, Departemen
from .departemen import departemen_widget, get_departemen_list

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
    departemen_name = colander.SchemaNode(
        colander.String(),
        field=Departemen.nama)


class AddSchema(colander.Schema):
    user_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.SelectWidget(values=User.get_list()),
        oid="user_id",
        title="User",
    )
    departemen_id = colander.SchemaNode(
        colander.Integer(),
        widget=departemen_widget,
        oid="departemen_id",
        title="Departemen", )


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
        self.list_route = 'user-departemen'
        self.table = DepartemenUser

    def list_join(self, query, **kwargs):
        return query.outerjoin(Departemen, Departemen.id == self.table.departemen_id) \
            .outerjoin(User, User.id == self.table.user_id)

    @view_config(route_name='user-departemen', renderer='templates/table.pt',
                 permission='user-view')
    def view_list(self, **kwargs):
        return super().view_list(**kwargs)

    @view_config(route_name='user-departemen-act', renderer='json',
                 permission='user-view')
    def view_act(self):
        return super().view_act()

    def get_bindings(self, row=None):
        return {"departemen_list": get_departemen_list()}

    @view_config(route_name='user-departemen-add', renderer='templates/form.pt',
                 permission='user-edit')
    def view_add(self):
        return super().view_add()

    @view_config(route_name='user-departemen-view', renderer='templates/form.pt',
                 permission='user-view')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='user-departemen-delete', renderer='templates/form.pt',
                 permission='user-edit')
    def view_delete(self):
        return super().view_delete()

    @view_config(route_name='user-departemen-edit', renderer='templates/form.pt',
                 permission='user-edit')
    def view_edit(self):
        return super().view_edit()
