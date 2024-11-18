import colander
from deform import (widget, )
from pyramid.i18n import TranslationStringFactory

from opensipkd.models import Menus, flush
from pyramid.view import (view_config, )
from sqlalchemy.orm import aliased

from ..views import ColumnDT, DataTables, BaseView
from .. import get_urls
_ = TranslationStringFactory("opensipkd")

SESS_ADD_FAILED = 'Tambah menu gagal'
SESS_EDIT_FAILED = 'Edit menu gagal'


def get_menu_list():
    q = Menus.get_list()
    return [(str(row.id), f"{row.kode}/ {row.nama}") for row in q]


@colander.deferred
def menu_widget(node, kw):
    values = kw.get('menu_list', [])
    return widget.Select2Widget(values=values)


class AddSchema(colander.Schema):
    # parent_id = colander.SchemaNode(
    #     colander.Integer(),
    #     widget=widget.HiddenWidget(), oid="parent_id", missing=colander.drop,
    # )
    #
    # parent_nm = colander.SchemaNode(
    #     colander.String(), missing=colander.drop,
    #     widget=widget.AutocompleteInputWidget(
    #         size=60, min_length=3,
    #         requirements=(("typeahead", None), ("deform", None),
    #                       {"js": "opensipkd.base:static/js/form/menu.js"})
    #     ),
    #     oid="parent_nm", title="Parent")
    # parent_kd = colander.SchemaNode(colander.String(),
    #                                 widget=widget.TextInputWidget(css_class="readonly"),
    #                                 missing=colander.drop, oid="parent_kd", title="Kode Induk")

    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    nama = colander.SchemaNode(colander.String(), oid="nama")
    valu = colander.SchemaNode(colander.String(), oid="valu",
                               title="Action",
                               missing=colander.drop)
    meth = colander.SchemaNode(colander.String(), oid="meth",
                               title="Method",
                               missing=colander.drop)
    page_typ = colander.SchemaNode(colander.String(), oid="page_typ",
                               title="Page Type")

    icon = colander.SchemaNode(colander.String(),
                               missing=colander.drop)
    class_name = colander.SchemaNode(colander.String(), oid="url",
                                     missing=colander.drop)
    need_login = colander.SchemaNode(colander.Integer(),
                                     widget=widget.RadioChoiceWidget(
                                         values=(("-1", "Unlogged"),
                                                 ("0", "All"),
                                                 ("1", "Logged User"),
                                                 )))
    title = colander.SchemaNode(colander.String())
    status = colander.SchemaNode(colander.Boolean(), oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        # self["parent_nm"] = colander.SchemaNode(
        #     colander.String(),
        #     missing=colander.drop,
        #     widget=AutocompleteInputWidget(
        #         size=60, min_length=3,
        #         values=f"{request.route_url('menu')}/hon/act"),
        #     oid="parent_nm",
        #     title="Induk", )
        # self["parent_nm"].widget = widget.AutocompleteInputWidget(
        #     size=60, min_length=3,
        #     requirements=(("typeahead", None), ("deform", None),
        #                   {"js": "opensipkd.base:static/js/form/menu.js"}),
        #     values=f"{request.route_url('menu')}/hon/act")
        # if request.user.company_id:
        #     self["company_id"].widget = widget.HiddenWidget()
        # self["company_id"].default = request.user.company_id


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.Integer(),
                             title=_("action", default="Action"))
    module= colander.SchemaNode(colander.String(), title="Kode", width='100pt')
    kode = colander.SchemaNode(colander.String(), title="Kode", width='100pt')
    nama = colander.SchemaNode(colander.String(), title="Nama")
    permission = colander.SchemaNode(colander.String(), title="Permission")
    status = colander.SchemaNode(colander.Boolean(), title="Status",
                                 width='50pt')
    need_login = colander.SchemaNode(colander.Integer(), title="Login",
                                     width='50pt')
    valu = colander.SchemaNode(colander.String(), title="Value",
                               width='50pt')
    meth = colander.SchemaNode(colander.String(), title="Method",
                               width='50pt')
    page_typ = colander.SchemaNode(colander.String(), title="Type",
                               width='50pt')
    level_id = colander.SchemaNode(colander.String(), title="Level",
                                   width='50pt')
    parent = colander.SchemaNode(colander.String(), title="Induk",
                                 width='200pt')


class ViewMenus(BaseView):
    def __init__(self, request):
        super(ViewMenus, self).__init__(request)
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Menus
        self.list_route = 'menu'
        self.form_scripts = ""

    def form_validator(self, form, value):
        def err_kode():
            raise colander.Invalid(form, 'Kode %s sudah digunakan oleh %s' % (
                value['kode'], found.nama))

        def err_nama():
            raise colander.Invalid(form,
                                   'Uraian %s sudah digunakan oleh kode %s' % (
                                       value['nama'], found.kode))

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = Menus.query_id(uid)
            current = q.first()
        else:
            current = None

        found = Menus.query_kode(value['kode']).first()
        if current:
            if found and found.id != current.id:
                err_kode()
        elif found:
            err_kode()

        found = Menus.query_nama(value['nama']).first()
        if current:
            if found and found.id != current.id:
                err_nama()
        elif found:
            err_nama()

    def update_children(self, children):
        for child in children:
            child.level_id = child.parent.level_id + 1
            flush(child)
            if child.children:
                self.update_children(child.children)

    def save_request(self, values, row=None):  # save(self, row, values):
        # for k, v in values.items():
        #     if not v:
        #         setattr(row, k, None)
        # row = super().save_request(values, row)
        for k, v in self.req.GET.items():
            if k not in values:
                if v:
                    values[k] = v
        values["status"] = "status" in values and values["status"] or 0
        return self.save(values, self.req.user, row)

    @view_config(route_name='menu',
                 renderer='templates/table.pt',
                 permission='menu')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='menu-view',
                 renderer='templates/form.pt', permission='menu')
    def view_view(self):
        return super(ViewMenus, self).view_view()

    @view_config(route_name='menu-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req

        params = request.params
        url_dict = request.matchdict
        table_alias = aliased(Menus)
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(Menus.id, mData='id'),
                       ColumnDT(Menus.kode, mData='kode'),
                       ColumnDT(Menus.nama, mData='nama'),
                       ColumnDT(table_alias.nama, mData='parent'),
                       ColumnDT(Menus.status, mData='status'),
                       ColumnDT(Menus.need_login, mData='need_login'),
                       ColumnDT(Menus.level_id, mData='level_id'),
                       ColumnDT(Menus.meth, mData='meth'),
                       ColumnDT(Menus.valu, mData='valu'),
                       ColumnDT(Menus.page_typ, mData='page_typ'), ]
            query = Menus.query_grid() \
                .outerjoin(table_alias, Menus.parent_id == table_alias.id)
            query = self.filter_company(query)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()
        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = Menus.query(). \
                filter(Menus.status == 1,
                       Menus.nama.ilike('%%%s%%' % term)) \
                .order_by(
                Menus.nama)
            return [dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id) for k in q.all()]

    @view_config(route_name='menu-add', renderer='templates/form.pt',
                 permission='menu')
    def view_add(self):
        return super(ViewMenus, self).view_add()

    @view_config(route_name='menu-edit',
                 renderer='templates/form.pt', permission='menu')
    def view_edit(self):
        return super(ViewMenus, self).view_edit()

    @view_config(route_name='menu-delete',
                 renderer='templates/form.pt', permission='menu')
    def view_delete(self):
        return super(ViewMenus, self).view_delete()