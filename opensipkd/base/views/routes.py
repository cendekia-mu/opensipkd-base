import colander
from deform import (widget, )
from opensipkd.tools.buttons import btn_view, btn_edit, btn_delete
from pyramid.view import view_config

from . import BaseView
from ..models import (DBSession, Route, )


class EditSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(), widget=widget.HiddenWidget())
    path = colander.SchemaNode(
        colander.String(), title='Path')
    nama = colander.SchemaNode(
        colander.String(), title='Nama')


class ListSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(), widget=widget.HiddenWidget(), visible=False)
    kode = colander.SchemaNode(
        colander.String())
    nama = colander.SchemaNode(
        colander.String(), title='Nama')
    path = colander.SchemaNode(
        colander.String(), title='Path')
    type = colander.SchemaNode(
        colander.String(), width="50pt")


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'routes'
        self.list_route = 'routes'
        self.list_buttons=(btn_view, btn_edit, btn_delete)
        # self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Route
        self.list_schema = ListSchema

    @view_config(
        route_name='routes', renderer='templates/table.pt',
        permission='edit-title')
    def view_list(self):
        return super().view_list()

    def form_validator(self, form, values):
        def err_nama():
            raise colander.Invalid(
                form,
                'Nama %s sudah digunakan oleh ID %s' % (values['nama'], found.id)
            )

        def err_kode():
            raise colander.Invalid(
                form,
                'Kode %s sudah digunakan oleh ID %s' % (values['kode'], found.id)
            )

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Route).filter_by(id=uid)
            row = q.first()
        else:
            row = None

        # cek nama
        q = Route.query(). \
            filter_by(nama=values['nama'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_nama()
        elif found:
            err_nama()

        # cek kode
        q = Route.query(). \
            filter_by(kode=values['kode'])
        found = q.first()
        if row:
            if found and found.id != row.id:
                err_kode()
        elif found:
            err_kode()

    @view_config(
        route_name='routes-act', renderer='json', permission='edit-title')
    def routes_act(self):
        return super().view_act()

    @view_config(
        route_name='routes-edit', renderer='templates/form.pt',
        permission='edit-title')
    def view_edit(self):
        return super().view_edit()
