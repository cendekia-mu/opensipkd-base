import colander
from deform import (widget, )
from opensipkd.models import DBSession, Departemen
from opensipkd.tools.buttons import btn_upload
from ..views import BaseView
# , get_urls
SESS_ADD_FAILED = 'Tambah departemen gagal'
SESS_EDIT_FAILED = 'Edit departemen gagal'


def get_departemen_list():
    r = [("", "--Pilih Departemen--")]
    q = DBSession.query(Departemen).order_by(Departemen.nama)
    for row in q:
        g = (str(row.id), (f"{row.kode}/ {row.nama}"))
        r.append(g)
    return r


@colander.deferred
def departemen_widget(node, kw):
    values = kw.get('departemen_list', [])
    return widget.Select2Widget(values=values, placeholder="Pilih Departemen")


def departemen_widget_form():
    return widget.AutocompleteInputWidget(
        size=60, min_length=3,
        requirements=(("typeahead", None), ("deform", None),
                      {"js": "opensipkd.base:static/js/form/departemen_form.js"}),
    )


class AddSchema(colander.Schema):
    parent_id = colander.SchemaNode(
        colander.Integer(),
        widget=widget.HiddenWidget(), oid="parent_id", missing=colander.drop,
    )
    parent_nm = colander.SchemaNode(
        colander.String(), missing=colander.drop,
        widget=widget.AutocompleteInputWidget(
            size=60, min_length=3,
            requirements=(("typeahead", None), ("deform", None),
                          {"js": "opensipkd.base:static/js/form/departemen.js"}),
            # options={"allowClear": True}
        ),
        oid="parent_nm", title="Induk")
    parent_kd = colander.SchemaNode(colander.String(),
                                    widget=widget.TextInputWidget(
                                        css_class="readonly"),
                                    missing=colander.drop, oid="parent_kd", title="Kode Induk")
    kode = colander.SchemaNode(colander.String(),
                               validator=colander.Length(max=32), oid="kode")
    nama = colander.SchemaNode(colander.String(), oid="nama")
    singkat = colander.SchemaNode(colander.String(), missing=colander.drop,
                                  oid="singkat")
    kategori = colander.SchemaNode(colander.String(), missing=colander.drop,
                                   oid="kategori")
    alamat = colander.SchemaNode(colander.String(), missing=colander.drop,
                                 oid="alamat")
    # company_id = colander.SchemaNode(colander.Integer(),
    #                                  widget=company_widget,
    #                                  missing=colander.drop,
    #                                  oid="company_id")
    status = colander.SchemaNode(colander.Integer(), 
                                 widget=widget.CheckboxWidget(true_val="1", false_val="0"),
                                 oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        self["parent_nm"].widget = widget.AutocompleteInputWidget(
            size=60, min_length=3,
            requirements=(("typeahead", None), ("deform", None),
                          {"js": "opensipkd.base:static/js/form/departemen.js"}),
            values=f"{request.route_url('base-departemen')}/hon/act",
        )
        # if request.user.company_id:
        #     self["company_id"].widget = widget.HiddenWidget()
        # self["company_id"].default = request.user.company_id


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="Action", visible=False)
    kode = colander.SchemaNode(colander.String(), title="Kode",
                               global_search=True,)
    nama = colander.SchemaNode(colander.String(), title="Nama",
                               global_search=True,)
    status = colander.SchemaNode(colander.Boolean(), title="Status", width='50pt',
                                 widget=widget.CheckboxWidget())
    level_id = colander.SchemaNode(
        colander.Integer(), title="Level", width='40pt')
    parent_id = colander.SchemaNode(colander.String(), title="Induk")
    # company_nm = colander.SchemaNode(colander.String(), title="Company")
    def after_bind(self, schema, kw):
        request = kw.get('request')
        schema["parent_id"].widget = widget.Select2Widget(
            values=get_departemen_list())

class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Departemen
        self.list_route = 'base-departemen'
        self.form_scripts = ""
        self.list_buttons = self.list_buttons + (btn_upload,)

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
            q = self.table.query().filter_by(id=uid)
            current = q.first()
        else:
            current = None
        found = self.table.query().filter_by(kode=value['kode']).first()

        # if "company_id" in value and value["company_id"]:
        #     found = found.filter_by(company_id=value["company_id"]).first()
        # else:
        #     found = self.filter_company(found).first()
        # if current:
        #     if found and found.id != current.id:
        #         err_kode()
        # elif found:
        #     err_kode()
        found = Departemen.query_nama(value['nama'])
        # if "company_id" in value and value["company_id"]:
        #     found = found.filter_by(company_id=value["company_id"]).first()
        # else:
        #     found = self.filter_company(found).first()
        # if current:
        #     if found and found.id != current.id:
        #         err_nama()
        # elif found:
        #     err_nama()
        super().form_validator(form, value)


    def update_children(self, children):
        for child in children:
            child.level_id = child.parent.level_id + 1
            DBSession.add(child)
            DBSession.flush()
            if child.children:
                self.update_children(child.children)

    def save_request(self, values, row=None):  # save(self, row, values):
        for k, v in values.items():
            if not v:
                setattr(row, k, None)
        values["level_id"] = 1
        if "parent_id" in values and values["parent_id"]:
            qry_parent = self.table.query_id(values["parent_id"])
            parent = qry_parent.first()
            if parent and parent.level_id:
                values["level_id"] = parent.level_id + 1
        if "parent_id" not in values:
            values["parent_id"] = None
        row = super().save_request(values, row)
        return row
    def view_act(self):
        request = self.req
        params = request.params
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            query = Departemen.cte_get()
            data = [{"id": d.id, "kode": d.kode, 
                     "nama": d.hierarchy.startswith(
                         '/') and d.hierarchy[1:] or d.hierarchy,
                     "status": d.status,
                     "level_id": d.lvl, "parent_id": d.parent_id} for d in query]
            return {
                
                "data": data}
        else:
            return self.next_act()

    def next_act(self):
        request = self.req
        params = request.params
        url_dict = request.matchdict
        if url_dict['act'] == 'hon':
            term = params.get('term', '')
            # q = Departemen.cte_get(search=term)

            q = DBSession.query(Departemen). \
                filter(Departemen.status == 1,
                       Departemen.nama.ilike(f'%{term}%')) \
                .order_by(Departemen.nama)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=f"{k.kode}:{k.nama}", kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

    

    def get_values(self, row, values=None):
        if not values:
            values = row.to_dict()
        if 'parent_id' in values and values['parent_id']:
            parent = row.parent
            values["parent_nm"] = parent.nama
            values["parent_kd"] = parent.kode
        return values
    # def save_upload(self, kode, csv_row):
    #     row = Departemen.query_kode(kode).first()
    #     if not row:
    #         row = Departemen()
    #         row.created = datetime.now()
    #         row.create_uid = self.req.user.id
    #         row.level_id = kode.count('.') + 1
    #         row.status = 1
    #     else:
    #         row.updated = datetime.now()
    #         row.update_uid = self.req.user.id
    #     row.kode = kode
    #     row.nama = csv_row['nama']
    #     DBSession.add(row)
    #     return row
