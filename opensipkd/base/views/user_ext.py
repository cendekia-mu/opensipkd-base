import colander
from datatables import (ColumnDT, DataTables, )
from deform import (widget, )
from opensipkd.tools.buttons import btn_close, btn_delete, btn_view
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config

from . import BaseView
from opensipkd.models import (DBSession, User, ExternalIdentity)

_ = TranslationStringFactory('user')


class AddSchema(colander.Schema):
    external_user_name = colander.SchemaNode(
        colander.String(), title=_('User Name'))
    provider_name = (colander.SchemaNode(colander.String(), title=_('Provider')))
    local_user_id = (colander.SchemaNode(colander.String(), title=_('User ID')))


class EditSchema(AddSchema):
    external_id = colander.SchemaNode(colander.String(),
                                      widget=widget.TextInputWidget(readonly=True),
                                      missing=colander.drop)


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), field="external_id", title="Action")
    external_user_name = colander.SchemaNode(
        colander.String(), title=_('User Name'))
    provider_name = (colander.SchemaNode(colander.String(), title=_('Provider')))
    local_user_id = (colander.SchemaNode(colander.String(), title=_('User ID')))


class UserExt(BaseView):
    def __init__(self, request):
        super(UserExt, self).__init__(request)
        self.edit_schema = EditSchema
        self.list_schema = ListSchema
        self.list_route = "user-ext"
        self.list_buttons = (btn_close,)
        self.table = ExternalIdentity

    @view_config(
        route_name='user-ext', renderer='templates/table.pt',
        permission='user-view')
    def view_list(self):
        form = super(UserExt, self).view_list(allow_edit=False, allow_delete=False)
        return form

    @view_config(
        route_name='user-ext-view', renderer='templates/form.pt',
        permission='user-view')
    def view_view(self):
        return super(UserExt, self).view_view()

    @view_config(
        route_name='user-ext-delete', renderer='templates/form.pt',
        permission='user-edit')
    def view_delete(self):
        return super(UserExt, self).view_delete()

    @view_config(
        route_name='user-ext-act', renderer='json', permission='user-view')
    def view_act(self):
        return super(UserExt, self).view_act()

    def delete_msg(self, row):
        return f'Data ID {row.external_id} sudah dihapus.'

    def query_id(self):
        return DBSession.query(ExternalIdentity).filter_by(external_id=self.req.matchdict["id"])
