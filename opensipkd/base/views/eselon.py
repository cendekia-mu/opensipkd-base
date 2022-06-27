import colander
from deform import (
    widget,
)
from pyramid.view import (
    view_config,
)

from .partner_base import NamaSchema
from ..models import (
    DBSession,
    Eselon
)
from ..views import BaseView

SESS_ADD_FAILED = 'Tambah eselon gagal'
SESS_EDIT_FAILED = 'Edit eselon gagal'


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode")
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    status = colander.SchemaNode(
        colander.Boolean(),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())

class ListSchema(NamaSchema):
    id = colander.SchemaNode(colander.String(),visible=False)

class Views(BaseView):
    def __init__(self, request):
        super(Views, self).__init__(request)
        self.form_params = dict(scripts="")
        self.list_url = 'eselon'
        self.list_route = 'eselon'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Eselon
        self.list_schema = ListSchema

    @view_config(route_name='eselon', renderer='templates/table.pt',
                 permission='eselon')
    def view_list(self):
        return super(Views, self).view_list()

    @view_config(route_name='eselon-act', renderer='json',
                 permission='read')
    def view_act(self):
        return super(Views, self).view_act()

    def next_act(self):
        params = self.params
        url_dict = self.req.matchdict
        if url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            qry = Eselon.query(). \
                filter(Eselon.kode.ilike('%%%s%%' % term)). \
                order_by(Eselon.kode)

            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.kode,
                    nama=row.nama
                )
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            prefix = 'prefix' in params and params['prefix'] or ''
            qry = Eselon.query(). \
                filter(Eselon.nama.ilike('%%%s%%' % term)). \
                order_by(Eselon.nama)
            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.nama,
                    kode=row.kode,
                )
                r.append(d)
            return r

    @view_config(route_name='eselon-add', renderer='templates/form.pt',
                 permission='eselon')
    def view_add(self):
        return super().view_add()
    @view_config(route_name='eselon-edit', renderer='templates/form.pt',
                 permission='eselon')
    def view_edit(self):
        return super().view_edit()

    @view_config(route_name='eselon-view', renderer='templates/form.pt',
                 permission='eselon')
    def view_view(self):
        return super().view_view()

    @view_config(route_name='eselon-delete', renderer='templates/form_input.pt',
                 permission='eselon')
    def view_delete(self):
        return super().view_delete()

    def form_validator(self, form, value):
        def err_kode():
            raise colander.Invalid(form,
                                   'Kode %s sudah digunakan oleh %s' % (
                                       value['kode'], found.nama))

        def err_nama():
            raise colander.Invalid(form,
                                   'Nama %s sudah digunakan oleh kode %s' % (
                                       value['nama'], found.kode))

        # edit
        def err_ruang():
            raise colander.Invalid(form,
                                   'Nama ruang %s tidak boleh lebih dari 1 karakter.' % (
                                       value['ruang']))

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Eselon).filter_by(id=uid)
            eselon = q.first()
        else:
            eselon = None

        q = Eselon.query_kode(value['kode'])
        found = q.first()
        if eselon:
            if found and found.id != eselon.id:
                err_kode()
        elif found:
            err_kode()

        found = Eselon.query_nama(value['nama']).first()
        if eselon:
            if found and found.id != eselon.id:
                err_nama()
        elif found:
            err_nama()
