import csv
import json
import os
import shutil
from datetime import datetime

import colander
from deform import (Form, widget, ValidationFailure, )
from deform.widget import AutocompleteInputWidget
from opensipkd.base.models import DepartemenUser
from pyramid.httpexceptions import (HTTPFound, )
from pyramid.view import (view_config, )
from sqlalchemy import func
from sqlalchemy.orm import aliased
from opensipkd.tools import (get_ext, get_random_string, get_settings)
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_delete, btn_close

from .upload import AddSchema as UploadSchema
from ..models import DBSession, Departemen
from ..views import ColumnDT, DataTables, BaseView

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

class AddSchema(colander.Schema):
    parent_id = colander.SchemaNode(colander.Integer(),
        widget=widget.HiddenWidget(), oid="parent_id", missing=colander.drop, )

    parent_nm = colander.SchemaNode(colander.String(), missing=colander.drop,
        widget=AutocompleteInputWidget(size=60, min_length=3, ),
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

    status = colander.SchemaNode(colander.Boolean(), oid="status")

    def after_bind(self, schema, kwargs):
        request = kwargs["request"]
        self["parent_nm"] = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=AutocompleteInputWidget(size=60, min_length=3,
                values=f"{request._host}/departemen/hon/act"), oid="parent_nm",
            title="Induk", )


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(), missing=colander.drop,
        widget=widget.HiddenWidget(readonly=True))


class ViewDepartemen(BaseView):
    def __init__(self, request):
        super(ViewDepartemen, self).__init__(request)
        self.form_scripts = """
         $('#parent_nm').bind('typeahead:selected', function(obj, datum) {
              $('#parent_id').val(datum.id);
              $('#parent_kd').val(datum.kode);

        });"""

        self.list_col_defs = json.dumps(
            [{"searchable": False, "visible": False, "targets": [0], }, {
                "searchable": True, "orderable": True, "targets": [1, 2],
            }])
        self.list_cols = [{'title': "ID", 'data': "id"},
                          {'title': "Kode", 'data': "kode", 'width': '100pt'},
                          {'title': "Nama", 'data': "nama"}, ]
        self.list_buttons = 'btn_view, btn_add, btn_edit, btn_delete, ' \
                            'btn_close'
        self.form_params = dict(scripts="")
        self.list_url = 'departemen'
        self.list_route = 'departemen'

    ########
    # List #
    ########
    @staticmethod
    def form_validator(form, value):
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
            urusan = q.first()
        else:
            urusan = None

        q = Departemen.query_kode(value['kode'])
        found = q.first()
        if urusan:
            if found and found.id != urusan.id:
                err_kode()
        elif found:
            err_kode()

        found = Departemen.query_nama(value['nama']).first()
        if urusan:
            if found and found.id != urusan.id:
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

    def save(self, values, user, row=None):
        if not row:
            row = Departemen()
            row.created = datetime.now()
            row.create_uid = user.id
        if 'parent_id' in values and not values['parent_id']:
            del values['parent_id']

        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = user.id
        row.status = 'status' in values and values['status'] and 1 or 0
        row.level_id = 1
        DBSession.add(row)
        DBSession.flush()
        if row.parent_id:
            row.level_id = (row.parent.level_id or 0) + 1

        DBSession.add(row)
        if row.children:
            for child in row.children:
                child.level_id = child.parent.level_id + 1
                DBSession.add(child)
        DBSession.flush()

        return row

    def save_request(self, values, row=None):
        request = self.req
        if 'id' in request.matchdict:
            values['id'] = request.matchdict['id']
        row = self.save(values, request.user, row)
        request.session.flash(
            "Departemen {nama} sudah disimpan.".format(nama=row.nama))

    def route_list(self, ):
        return HTTPFound(location=self.req.route_url(self.list_route))

    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel)):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(request=self.req)
        schema.request = self.req
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons)

    def session_failed(self, session_name):
        r = dict(form=self.req.session[session_name])
        del self.req.session[session_name]
        return r

    def query_id(self):
        return DBSession.query(Departemen).filter_by(
            id=self.req.matchdict['id'])

    def id_not_found(self):
        msg = 'Departemen ID %s Tidak Ditemukan.' % self.req.matchdict['id']
        self.req.session.flash(msg, 'error')
        return self.route_list()

    @view_config(route_name='departemen-view',
                 renderer='templates/form_input.pt', permission='departemen')
    def view_view(self):  # row = query_id(request).first()
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()

        form = self.get_form(EditSchema, buttons=(btn_close,))
        if request.POST:
            return self.route_list()

        form.set_appstruct(self.get_values(row))
        return dict(form=form.render(readonly=True), scripts=self.form_scripts)

    @view_config(route_name='departemen',
                 renderer='templates/list.pt',
                 permission='departemen')
    def view_list(self):
        return super().view_list()

    ##########
    # Action #
    ##########
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
                ColumnDT(Departemen.level_id, mData='level_id'), ]
            query = DBSession.query().select_from(Departemen).outerjoin(
                dep_alias, Departemen.parent_id == dep_alias.id)
            row_table = DataTables(request.GET, query, columns)
            return row_table.output_result()

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Departemen).filter(Departemen.status == 1,
                                                   Departemen.nama.ilike(
                                                       '%%%s%%' %
                                                       term)).order_by(
                Departemen.nama)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

        elif url_dict['act'] == 'honk':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Departemen).filter(Departemen.status == 1,
                                                   func.concat(Departemen.nama,
                                                               ';',
                                                               Departemen.kode).ilike(
                                                       '%%%s%%' %
                                                       term)).order_by(
                Departemen.nama)
            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama + ';' + k.kode, kode=k.kode,
                         nama=k.nama, level_id=k.level_id)
                r.append(d)
            return r

        elif url_dict['act'] == 'hon_level':
            term = 'term' in params and params['term'] or ''
            settings = get_settings()
            level_id = 'departemen_chg_id' in settings and settings[
                'departemen_chg_id'] or 0
            q = DBSession.query(Departemen).filter(Departemen.status == 1,
                                                   Departemen.nama.ilike(
                                                       '%%%s%%' %
                                                       term)).order_by(
                Departemen.nama)
            if int(level_id) > 0:
                q = q.filter(Departemen.level_id == int(level_id))
            if request.user.id > 1 and not request.has_permission(
                    "departemen-all"):
                user_dep = DepartemenUser.query_user_id(request.user.id).first()
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
            if int(level_id) > 0:
                q = q.filter(Departemen.level_id == int(level_id))

            rows = q.all()
            r = []
            for k in rows:
                d = dict(id=k.id, value=k.nama, kode=k.kode, nama=k.nama,
                         level_id=k.level_id)
                r.append(d)
            return r

    @view_config(route_name='departemen-add',
                 renderer='templates/form_input.pt', permission='departemen')
    def view_add(self):
        request = self.req
        form = self.get_form(AddSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.render(appstruct=e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)
                self.save_request(dict(controls))
            return self.route_list()
        return dict(form=form.render(), scripts=self.form_scripts)

    ########
    # Edit #
    ########
    @view_config(route_name='departemen-edt',
                 renderer='templates/form_input.pt', permission='departemen')
    def view_edt(self):
        request = self.req
        row = self.query_id().first()
        if not row:
            return self.id_not_found()

        form = self.get_form(EditSchema)
        if request.POST:
            if 'save' in request.POST:
                controls = request.POST.items()
                try:
                    controls = form.validate(controls)
                except ValidationFailure as e:
                    form.set_appstruct(e.cstruct)
                    return dict(form=form.render(), scripts=self.form_scripts)

                self.save_request(dict(controls), row)
            return self.route_list()
        form.set_appstruct(self.get_values(row))
        return dict(form=form.render(), scripts=self.form_scripts)

    ##########
    # Delete #
    ##########
    @view_config(route_name='departemen-del',
                 renderer='templates/form_input.pt', permission='departemen')
    def view_delete(self):
        request = self.req
        q = self.query_id()
        row = q.first()
        if not row:
            return self.id_not_found()
        if request.POST:
            if 'delete' in request.POST:
                msg = 'Departemen ID %d %s sudah dihapus.' % (row.id, row.nama)
                q.delete()
                DBSession.flush()
                request.session.flash(msg)
            return self.route_list()
        form = self.get_form(EditSchema,
                             buttons=(btn_delete, btn_cancel))
        form.set_appstruct(self.get_values(row))
        return dict(form=form.render(readonly=True), scripts=self.form_scripts)

    ##########
    # Upload #
    ##########
    @view_config(route_name='departemen-upload',
                 renderer='templates/departemen/upload.pt',
                 permission='departemen')
    def view_upload(self):
        request = self.req
        form = self.get_form(UploadSchema)
        if request.POST:
            if 'save' in request.POST:
                # settings = get_settings()
                input_file = request.POST['upload'].file
                filename = request.POST['upload'].filename
                ext = get_ext(filename)
                if ext.lower() != '.csv':
                    request.session.flash('File harus format csv', 'error')
                    return dict(form=form.render())
                if not input_file:
                    return dict(form=form.render())
                input_file.seek(0)
                temp_file_path = '/tmp/' + get_random_string(10) + '.csv'

                with open(temp_file_path, 'wb') as output_file:
                    shutil.copyfileobj(input_file, output_file)

                with open(temp_file_path) as f:
                    c = csv.DictReader(f)
                    for csv_row in c:
                        kode = csv_row['kode']
                        if kode:
                            xcode = kode.split(".")
                            for r in range(len(xcode)):
                                xc = xcode[r] and int(xcode[r])
                                if not xc and type(xc) == int:
                                    code = ""
                                    for t in range(r):
                                        code += xcode[t] + '.'

                                    if code:
                                        code = code[:-1]
                                        save_upload(request, code, csv_row)

                            save_upload(request, kode, csv_row)

                    DBSession.flush()
                os.remove(temp_file_path)

            return self.route_list()
        return dict(form=form.render())

    def get_values(self, row, values=None):
        if not values:
            values = row.to_dict()
        if 'parent_id' in values and values['parent_id']:
            parent = row.parent
            values["parent_nm"] = parent.nama
            values["parent_kd"] = parent.kode
        return values


def save_upload(request, kode, csv_row):
    row = Departemen.query_kode(kode).first()
    if not row:
        row = Departemen()
        row.created = datetime.now()
        row.create_uid = request.user.id
        row.level_id = kode.count('.') + 1
        row.status = 1
    else:
        row.updated = datetime.now()
        row.update_uid = request.user.id
    row.kode = kode
    row.nama = csv_row['nama']
    DBSession.add(row)
    return row