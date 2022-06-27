import json

import colander
from datatables import ColumnDT
from deform import Form, widget
from opensipkd.tools.buttons import btn_view, btn_delete
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from opensipkd.base import DBSession
from opensipkd.base.models.handlers import Log
from opensipkd.base.views import BaseView, DataTables


class AddSchema(colander.Schema):
    created_at = colander.SchemaNode(
        colander.DateTime())
    logger = colander.SchemaNode(
        colander.String())
    level = colander.SchemaNode(
        colander.String())
    trace = colander.SchemaNode(
        colander.String(),
        missing=colander.drop)
    msg = colander.SchemaNode(
        colander.String(),
        widget=widget.TextAreaWidget(rows=10, ),
        missing=colander.drop)


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             visible=False)
    created_at = colander.SchemaNode(
        colander.DateTime())
    logger = colander.SchemaNode(
        colander.String())
    level = colander.SchemaNode(
        colander.String())
    msg = colander.SchemaNode(
        colander.String(),
        widget=widget.TextAreaWidget(rows=10, ),
        missing=colander.drop)


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'log'
        self.list_route = 'log'
        self.list_buttons=(btn_view, btn_delete)
        # self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Log
        self.list_schema = ListSchema

    @view_config(route_name='log', renderer='templates/table.pt',
                 permission='log')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='log-act', renderer='json_rpc',
                 permission='log')
    def view_act(self):
        return super().view_act()

    @view_config(route_name='log-view', renderer='templates/form_input.pt',
                 permission='log')
    def view_view(self):
        return super().view_view()
