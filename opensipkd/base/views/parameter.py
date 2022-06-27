import colander
from deform import (widget, )
from pyramid.view import (view_config, )

from . import BaseView
from ..models import (
    DBSession,
    Parameter)

class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        oid="kode",
        title="Kode")

    nama = colander.SchemaNode(
        colander.String(),
        oid="nama",
        title="Nama")

    value = colander.SchemaNode(
        colander.String(),
        widget=widget.TextAreaWidget(rows=5),
        oid="value",
        title="Nilai")

    status = colander.SchemaNode(
        colander.Boolean())


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True),
                             visible=False)


class Views(BaseView):
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'parameter'
        self.list_route = 'parameter'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Parameter
        self.list_schema = EditSchema

    @view_config(route_name='parameter', renderer='templates/table.pt',
                 permission='user-edit')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='parameter-act', renderer='json',
                 permission='user-edit')
    def view_act(self):
        return super().view_act()

    def next_act(self):
        url_dict = self.req.matchdict
        params = self.params
        if url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            rows = DBSession.query(Parameter.id, Parameter.nama). \
                filter(Parameter.nama.ilike('%{term}%'.format(term=term))). \
                order_by(Parameter.nama).all()
            r = [dict(id=k[0], value=k[1]) for k in rows]
            return r

    @view_config(route_name='parameter-add', renderer='templates/form.pt',
                 permission='user-edit')
    def view_add(self):
        return super().view_add()

    @view_config(route_name='parameter-edit', renderer='templates/form.pt',
                 permission='user-edit')
    def view_edit(self):
        return super().view_edit()

    @view_config(route_name='parameter-view', renderer='templates/form.pt',
                 permission='user-view')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='parameter-delete', renderer='templates/form.pt',
                 permission='user-edit')
    def view_delete(self):
        return super().view_delete()
