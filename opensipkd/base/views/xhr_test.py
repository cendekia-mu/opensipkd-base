import colander
from deform import (widget, )
from opensipkd.base.models import TestModel
from . import base_views, api_base


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(colander.String(),
                               title="Kode",
                               widget=widget.TextInputWidget())
    nama = colander.SchemaNode(colander.String(),
                               title="Nama",
                               widget=widget.TextInputWidget())
    description = colander.SchemaNode(colander.String(),
                                      title="Description",
                                      widget=widget.TextInputWidget())

    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())
    


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(), title="Action")
    kode = colander.SchemaNode(colander.String(),
                               title="Kode",
                               widget=widget.TextInputWidget())
    nama = colander.SchemaNode(colander.String(),
                               title="Nama",
                               widget=widget.TextInputWidget())


class Views(base_views.BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_schema = ListSchema
        self.table = TestModel
        self.add_schema = AddSchema
        self.edit_schema = AddSchema
        self.list_route = 'base-xhr-test'


class ViewsApi(api_base.ApiViews):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table = TestModel
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = AddSchema

