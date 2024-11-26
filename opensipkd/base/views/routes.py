import logging

import colander
from deform import (widget, )
from opensipkd.models import (DBSession, Route, )
from opensipkd.tools.buttons import btn_view, btn_edit, btn_delete
from pyramid.view import view_config
from sqlalchemy.orm import aliased
from . import BaseView, get_urls

_logging = logging.getLogger(__name__)


@colander.deferred
def route_widget(node, kw):
    values = kw.get('route_list', [])
    return widget.AutocompleteInputWidget(values=values, placeholder="Pilih Induk")


def route_widget_form():
    return widget.AutocompleteInputWidget(
        size=60, min_length=3,
        requirements=(("typeahead", None), ("deform", None),
                      {"js": "opensipkd.base:static/js/form/departemen_form.js"}),
    )


class EditSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(), widget=widget.HiddenWidget())
    kode = colander.SchemaNode(
        colander.String(),)

    path = colander.SchemaNode(
        colander.String(), title='Path')
    nama = colander.SchemaNode(
        colander.String(), title='Nama')
    module = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Nama Aplikasi Untuk Filtering"
    )
    is_menu = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        widget=widget.CheckboxWidget(false_val="0", true_val="1"),
        label="Checklist jika path merupakan Menu")
    parent_id = colander.SchemaNode(
        colander.Integer(),
        # widget=widget.HiddenWidget,
        missing=colander.drop,
        oid="parent_id"
    )
    parent_nm = colander.SchemaNode(
        colander.String(),
        widget=route_widget,
        missing=colander.drop,
        oid="parent_nm"
    )

    order_id = colander.SchemaNode(
        colander.Integer(),
        missing=colander.drop,
        description="Pengurutan Menu")
    permission = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Nama permission untuk menentukan hak akses"
    )
    class_view = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Nama file tanpa extension yang berisi class Views")
    def_func = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        description="Nama fungsi dalam class"
    )
    template = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
        default="form.pt",
        descripton="Nama File template atau 'json' atau renderer")
    icon = colander.SchemaNode(
        colander.String(),
        missing=colander.drop,
    )

    type = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(false_val="0", true_val="1"),
        label="Checklist jika type url adalah json")
    status = colander.SchemaNode(
        colander.String(),
        widget=widget.CheckboxWidget(false_val="0", true_val="1"))

alias = aliased(Route)
class ListSchema(colander.Schema):
    id = colander.SchemaNode(
        colander.Integer(), widget=widget.HiddenWidget(), visible=False)
    kode = colander.SchemaNode(
        colander.String())
    parent = colander.SchemaNode(
        colander.String(),
        field=alias.kode)
    nama = colander.SchemaNode(
        colander.String(), title='Nama')
    path = colander.SchemaNode(
        colander.String(), title='Path')

    type = colander.SchemaNode(
        colander.String(), width="50pt")
    status = colander.SchemaNode(
        colander.Boolean(),
        widget=widget.CheckboxWidget(false_val="0", true_val="1"))


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'routes'
        self.list_route = 'routes'
        self.list_buttons = (btn_view, btn_edit, btn_delete)
        # self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Route
        self.list_schema = ListSchema
        self.form_scripts = """
          $('#parent_nm').bind('typeahead:selected', function (obj, datum, name) {
            $('#parent_id').val(datum.id);
            $('#parent_kd').val(datum.kode);
            console.log(datum.kode);
          });
        
          $('#parent_nm').on('input',
              function (e) {
                let val = $('#parent_nm').val();
                if (val === null || val === "") {
                  $('#parent_id').val("");
                  $('#parent_kd').val("");
                }
              });
        """

    @view_config(
        route_name='routes', renderer='templates/table.pt',
        permission='edit-title')
    def view_list(self):
        kwargs = {"allow_view": False,
                  "allow_delete": False}
        return super().view_list(**kwargs)

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
    def view_act(self):
        return super().view_act()

    @view_config(
        route_name='routes-edit', renderer='templates/form.pt',
        permission='edit-title')
    def view_edit(self):
        return super().view_edit()

    def next_act(self, **kwargs):
        row = kwargs.get("row")
        params = self.req.params
        url_dict = self.req.matchdict
        if url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = Route.query(). \
                filter(Route.status == 1,
                       Route.kode.ilike('%%%s%%' % term)) \
                .order_by(Route.kode)
            r = []
            for k in q.all():
                d = dict(id=k.id, value=k.kode, kode=k.kode, nama=k.nama)
                r.append(d)
            return r

    def get_bindings(self, row=None):
        return {"route_list": get_urls(f"{self.req.route_url('routes')}/hon/act")}

    def get_values(self, row, istime=False, null=False):
        values = super().get_values(row, istime, null)
        if row.parent_id:
            route = Route.query_id(row.parent_id).first()
            values["parent_nm"] = route and route.kode or ""
        _logging.debug(values)
        return values

    def list_join(self, query, **kwargs):
        return query.outerjoin(alias, Route.parent_id == alias.id)