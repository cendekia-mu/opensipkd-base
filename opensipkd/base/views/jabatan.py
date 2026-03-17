import os

import colander
from deform import (widget, )
from opensipkd.base.models import (
    DBSession, Jabatan, Eselon, Departemen)
from opensipkd.tools.report import (
    csv_response, open_rml_pdf, open_rml_row, pdf_response)
from pyramid.i18n import TranslationStringFactory

from ..views import BaseView

_ = TranslationStringFactory("opensipkd")

JENIS = ((1, _('structural', default='Structural')),
         (2, _('functional', default='Functional')),
         (3, _('finance', default='Finance')),
         )


def daftar_eselon():
    return DBSession.query(Eselon.id, Eselon.nama).order_by(Eselon.kode).all()


@colander.deferred
def deferred_eselon(node, kw):
    values = kw.get('daftar_eselon', [])
    return widget.SelectWidget(values=values)


class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode")
    nama = colander.SchemaNode(
        colander.String(),
        oid="nama")
    nama_pendek = colander.SchemaNode(
        colander.String(),
        oid="nama_pendek",
        missing=colander.drop)
    nama_lain = colander.SchemaNode(
        colander.String(),
        oid="nama_lain",
        missing=colander.drop)
    jenis = colander.SchemaNode(
        colander.Integer(),
        oid="jenis",
        widget = widget.SelectWidget(values=JENIS),
        title=_("type", default="Jenis"))
    eselon_id = colander.SchemaNode(
        colander.Integer(),
        oid="eselon_id",
        widget=deferred_eselon,
        title=_("eselon", default="Eselon"))
    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(true_val="1", false_val="0"),
        oid="status")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget())


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String(), title="Action")
    kode = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=32),
        oid="kode",
        title="Kode",
        width="100pt")
    nama = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=64),
        oid="nama")
    status = colander.SchemaNode(
        colander.Integer(),
        widget=widget.CheckboxWidget(),
        oid="status")


class Views(BaseView):
    def __init__(self, request):
        super().__init__(request)
        self.form_params = dict(scripts="")
        self.list_route = 'base-jabatan'
        self.add_schema = AddSchema
        self.edit_schema = EditSchema
        self.table = Jabatan
        self.list_schema = ListSchema
        # self.list_buttons = (btn_view, btn_add, btn_edit, btn_delete, btn_close)

    def get_bindings(self, row=None):
        return dict(daftar_jenis=JENIS,
                    daftar_eselon=daftar_eselon())

    def next_act(self):
        request = self.req
        params = request.params
        url_dict = request.matchdict
        if url_dict['act'] == 'hok':
            term = 'term' in params and params['term'] or ''
            qry = DBSession.query(Jabatan). \
                filter(Jabatan.status == 1). \
                filter(Jabatan.kode.ilike('%%%s%%' % term)). \
                order_by(Jabatan.kode)

            r = []
            for row in qry.all():
                d = dict(
                    id=row.id,
                    value=row.nama,
                    # value = row.nama,
                    # kode  = row.kode,
                    nama=row.kode
                )
                r.append(d)
            return r

        elif url_dict['act'] == 'hon':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama,
                                Jabatan.jenis). \
                filter(Jabatan.nama.ilike('%%%s%%' % term)). \
                order_by(Jabatan.nama)
            rows = q.all()
            r = []
            for k in rows:
                if k[3] == 1:
                    nama_jenis = 'Struktural'
                elif k[3] == 2:
                    nama_jenis = 'Fungsional'
                else:
                    nama_jenis = 'Keuangan'

                d = {}
                d['id'] = k[0]
                d['value'] = k[2] + ' (' + nama_jenis + ')'
                d['kode'] = k[1]
                d['nama'] = k[2]
                r.append(d)
            return r

        elif url_dict['act'] == 'headofnama':
            term = 'term' in params and params['term'] or ''
            q = DBSession.query(Jabatan.id, Jabatan.kode, Jabatan.nama,
                                Jabatan.jenis). \
                filter(Jabatan.nama.ilike('%%%s%%' % term)). \
                order_by(Jabatan.nama)
            rows = q.all()
            r = []
            for k in rows:
                if k[3] == 1:
                    nama_jenis = 'Keuangan'
                elif k[3] == 2:
                    nama_jenis = 'Struktural'
                else:
                    nama_jenis = 'Fungsional'

                d = {'id': k[0], 'value': k[2] + ' (' + nama_jenis + ')',
                     'kode': k[1], 'nama': k[2]}
                r.append(d)
            return r
        elif url_dict['act'] == 'csv':
            query = query_reg(request)
            row = query.first()
            header = row.keys()
            rows = []
            for item in query.all():
                rows.append(list(item))

            filename = 'jabatan.csv'
            value = {
                'header': header,
                'rows': rows,
            }
            return csv_response(request, value, filename)
        elif url_dict['act'] == 'pdf':
            query = query_reg(request)
            _here = os.path.dirname(__file__)  # get current folder -> views
            path = os.path.dirname(_here)  # mundur 1 level
            path = os.path.join(path, 'reports')
            rml_row = open_rml_row(path + '/jabatan.row.rml')

            rows = []
            for r in query.all():
                s = rml_row.format(kode=r.kode, nama=r.nama,
                                   status=r.status and "Aktif" or "Pasif")
                rows.append(s)

            pdf, filename = open_rml_pdf(path + '/jabatan.rml', rows=rows,
                                         company=request.company,
                                         departement=request.session[
                                             'departemen_nm'],
                                         address=request.address,
                                         alamat=Departemen.query_id(
                                             request.session[
                                                 'departemen_id']).first(),
                                         periode='01-01-2017 s.d 31-12-2017')
            return pdf_response(request, pdf, filename)

    def form_validator(self, form, value):
        def err_kode():
            raise colander.Invalid(form,
                                   'Kode %s sudah digunakan oleh %s' % (
                                       value['kode'], found.nama))

        def err_nama():
            raise colander.Invalid(form,
                                   'Uraian %s sudah digunakan oleh kode %s' % (
                                       value['nama'], found.kode))

        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Jabatan).filter_by(id=uid)
            jabatan = q.first()
        else:
            jabatan = None

        q = Jabatan.query_kode(value['kode'])
        # DBSession.query(Jabatan).filter_by(kode=value['kode'])
        found = q.first()
        if jabatan:
            if found and found.id != jabatan.id:
                err_kode()
        elif found:
            err_kode()

        found = Jabatan.query_nama(value['nama']).first()
        if jabatan:
            if found and found.id != jabatan.id:
                err_nama()
        elif found:
            err_nama()
        super().form_validator(form, value)



def query_reg(request):
    return DBSession.query(Jabatan.kode,
                           Jabatan.nama,
                           Jabatan.status, ). \
        filter(Jabatan.status == 1). \
        order_by(Jabatan.id)
