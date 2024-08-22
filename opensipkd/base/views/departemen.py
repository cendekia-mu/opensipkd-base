from datetime import datetime

import colander
from deform import (widget, )
from opensipkd.models import DBSession, Departemen, Partner, PartnerDepartemen, ResCompany
from opensipkd.tools import (get_settings)
from opensipkd.tools.buttons import btn_upload
from pyramid.view import (view_config, )
from sqlalchemy import func
from sqlalchemy.orm import aliased

from .company import company_widget
from .. import get_params
from ..views import ColumnDT, DataTables, BaseView, get_urls

SESS_ADD_FAILED = 'Tambah departemen gagal'
SESS_EDIT_FAILED = 'Edit departemen gagal'


def get_departemen_list():
    r = []
    q = DBSession.query(Departemen).order_by(Departemen.nama)
    for row in q:
        g = (str(row.id), (f"{row.kode}/ {row.nama}"))
        r.append(g)
    return r


@colander.deferred
def departemen_widget(node, kw):
    values = kw.get('departemen_list', [])
    return widget.Select2Widget(values=values)


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
                                    widget=widget.TextInputWidget(css_class="readonly"),
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
    company_id = colander.SchemaNode(colander.Integer(),
                                     widget=company_widget,
                                     missing=colander.drop,
                                     oid="company_id")

    status = colander.SchemaNode(colander.Boolean(), oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        self["parent_nm"].widget = widget.AutocompleteInputWidget(
            size=60, min_length=3,
            requirements=(("typeahead", None), ("deform", None),
                          {"js": "opensipkd.base:static/js/form/departemen.js"}),
            values=get_urls(f"{request.route_url('departemen')}/hon/act"),
        )

        if request.user.company_id:
            self["company_id"].widget = widget.HiddenWidget()
        self["company_id"].default = request.user.company_id


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
                             widget=widget.HiddenWidget(readonly=True))


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="Action", visible=False)
    kode = colander.SchemaNode(colander.String(), title="Kode")
    nama = colander.SchemaNode(colander.String(), title="Nama")
    status = colander.SchemaNode(colander.Boolean(), title="Status", width='50pt',
                                 widget=widget.CheckboxWidget())
    level_id = colander.SchemaNode(colander.Integer(), title="Level", width='40pt')
    parent = colander.SchemaNode(colander.String(), title="Induk")
    company_nm = colander.SchemaNode(colander.String(), title="Company")


class ViewDepartemen(BaseView):
    def __init__(self, request):
        super(ViewDepartemen, self).__init__(request)
        self.list_schema = ListSchema
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Departemen
        # self.list_url = 'departemen'
        self.list_route = 'departemen'
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
            q = DBSession.query(Departemen).filter_by(id=uid)
            current = q.first()
        else:
            current = None

        found = Departemen.query_kode(value['kode'])
        if "company_id" in value and value["company_id"]:
            found = found.filter_by(company_id=value["company_id"]).first()
        else:
            found = self.filter_company(found).first()
        if current:
            if found and found.id != current.id:
                err_kode()
        elif found:
            err_kode()

        found = Departemen.query_nama(value['nama'])
        if "company_id" in value and value["company_id"]:
            found = found.filter_by(company_id=value["company_id"]).first()
        else:
            found = self.filter_company(found).first()
        if current:
            if found and found.id != current.id:
                err_nama()
        elif found:
            err_nama()

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

    @view_config(route_name='departemen-view',
                 renderer='templates/form.pt', permission='departemen')
    def view_view(self):
        return super(ViewDepartemen, self).view_view()

    @view_config(route_name='departemen',
                 renderer='templates/table.pt',
                 permission='departemen')
    def view_list(self):
        return super().view_list()

    @view_config(route_name='departemen-act', renderer='json',
                 permission='view')
    def view_act(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        dep_alias = aliased(Departemen)
        if url_dict['act'] == 'grid':
            columns = [ColumnDT(Departemen.id, mData='id'),
                       ColumnDT(Departemen.kode, mData='kode'),
                       ColumnDT(Departemen.nama, mData='nama'),
                       ColumnDT(dep_alias.nama, mData='parent'),
                       ColumnDT(Departemen.status, mData='status'),
                       ColumnDT(Departemen.level_id, mData='level_id'),
                       ColumnDT(ResCompany.nama, mData='company_nm'), ]
            query = DBSession.query().select_from(Departemen).outerjoin(
                dep_alias, Departemen.parent_id == dep_alias.id).outerjoin(
                ResCompany, self.table.company_id == ResCompany.id
            )
            query = self.filter_company(query)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Departemen). \
                filter(Departemen.status == 1,
                       Departemen.nama.ilike('%%%s%%' % term)) \
                .order_by(
                Departemen.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

        elif url_dict['act'] == 'honk':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Departemen) \
                .filter(Departemen.status == 1,
                        func.concat(Departemen.nama, ';',
                                    Departemen.kode) \
                        .ilike('%%%s%%' % term)) \
                .order_by(Departemen.nama)
            q = self.filter_company(q)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama + ';' + k.kode, kode=k.kode,
                         nama=k.nama, level_id=k.level_id)
                r.append(d)
            return r

        elif url_dict['act'] == 'hon_level':
            # todo Check ulang untuk hon
            term = 'term' in params and params['term'] or ''
            settings = get_settings()
            level_id = get_params('departemen_chg_id', 0)
            q = DBSession.query(Departemen).filter(Departemen.status == 1,
                                                   Departemen.nama.ilike(
                                                       '%%%s%%' %
                                                       term)).order_by(
                Departemen.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            if int(level_id) > 0:
                q = q.filter(Departemen.level_id == int(level_id))
            if request.user.id > 1 and not request.has_permission(
                    "departemen-all"):
                partner = Partner.query_id(request.user.id).first()
                if partner:
                    PartnerDepartemen.query_jabatan(partner.id, datetime.now())
                user_dep = PartnerDepartemen.query_user_id().first()
                if not user_dep:
                    return []

                kode = user_dep.departemen.kode
                if user_dep.sub_departemen:
                    q = q.filter(Departemen.kode.ilike('{}%'.format(kode)))
                else:
                    q = q.filter(Departemen.kode == kode)

            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

        elif url_dict['act'] == 'hon_all':
            term = 'term' in params and params['term'] or ''
            settings = get_settings()
            level_id = 'departemen_chg_id' in settings and settings[
                'departemen_chg_id'] or 0
            q = DBSession.query(Departemen).filter(Departemen.status == 1,
                                                   Departemen.nama.ilike(
                                                       '%%%s%%' %
                                                       term)).order_by(
                Departemen.nama)
            if self.req.user.company_id:
                q = q.filter(Departemen.company_id == self.req.user.company_id)
            if int(level_id) > 0:
                q = q.filter(Departemen.level_id == int(level_id))

            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

    def get_bindings(self, row=None):
        return {"company_list": ResCompany.get_list()}

    @view_config(route_name='departemen-add', renderer='templates/form.pt',
                 permission='departemen')
    def view_add(self):
        return super(ViewDepartemen, self).view_add()

    @view_config(route_name='departemen-edit',
                 renderer='templates/form.pt', permission='departemen')
    def view_edit(self):
        return super(ViewDepartemen, self).view_edit()

    @view_config(route_name='departemen-delete',
                 renderer='templates/form.pt', permission='departemen')
    def view_delete(self):
        return super(ViewDepartemen, self).view_delete()

    @view_config(route_name='departemen-upload',
                 renderer='templates/departemen/upload.pt',
                 permission='departemen')
    def view_upload(self):
        return super().view_upload(exts=('.csv',), delimiter="\t")

        # request = self.req
        # form = self.get_form(UploadSchema)
        # if request.POST:
        #     if 'save' in request.POST:
        #         input_file = request.POST['upload'].file
        #         filename = request.POST['upload'].filename
        #         ext = get_ext(filename)
        #         if ext.lower() != '.csv':
        #             request.session.flash('File harus format csv', 'error')
        #             return dict(form=form.render())
        #         if not input_file:
        #             return dict(form=form.render())
        #         input_file.seek(0)
        #         temp_file_path = '/tmp/' + get_random_string(10) + '.csv'
        #
        #         with open(temp_file_path, 'wb') as output_file:
        #             shutil.copyfileobj(input_file, output_file)
        #
        #         with open(temp_file_path) as f:
        #             c = csv.DictReader(f)
        #             for csv_row in c:
        #                 kode = csv_row['kode']
        #                 if kode:
        #                     xcode = kode.split(".")
        #                     for r in range(len(xcode)):
        #                         xc = xcode[r] and int(xcode[r])
        #                         if not xc and type(xc) == int:
        #                             code = ""
        #                             for t in range(r):
        #                                 code += xcode[t] + '.'
        #
        #                             if code:
        #                                 code = code[:-1]
        #                                 self.save_upload(code, csv_row)
        #
        #                     self.save_upload(kode, csv_row)
        #
        #             DBSession.flush()
        #         os.remove(temp_file_path)
        #
        #     return self.route_list()
        # return dict(form=form.render())

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
