import os
from datetime import datetime

from pyramid.view import (
    view_config,
)

from opensipkd.models import DBSession as PartnerDBSession
from opensipkd.models import (
    Departemen,
    Jabatan,
    Partner,
    PartnerDepartemen
)
from opensipkd.tools import (dmy)
from opensipkd.tools.report import (
    open_rml_row,
    open_rml_pdf,
    pdf_response,
    csv_response,
)
from ..views import (BaseView)


#############
# CSV & PDF #
#############
class view_rpt(BaseView):
    @view_config(route_name='partner-departemen-rpt', renderer='csv')
    def view_csv(self):
        request = self.req
        ses = request.session
        params = request.params
        url_dict = request.matchdict
        uid = request.user.id
        tgl = datetime.now().strftime('%d-%m-%Y')
        if url_dict['rpt'] == 'csv':
            query = query_reg(request)
            row = query.first()
            header = row.keys()
            rows = []
            for item in query.all():
                rows.append(list(item))

            filename = 'posisi.csv'
            value = {
                'header': header,
                'rows': rows,
            }
            return csv_response(request, value, filename)
        elif url_dict['rpt'] == 'pdf':
            query = query_reg(request)
            _here = os.path.dirname(__file__)  # get current folder -> views
            path = os.path.dirname(_here)  # mundur 1 level
            path = os.path.join(path, 'reports')
            rml_row = open_rml_row(path + '/posisi.row.rml')

            rows = []
            for r in query.all():
                s = rml_row.format(nip=r.nik, nama=r.nama, organisasi=r.departemen, jabatan=r.jabatan,
                                   mulai=dmy(r.mulai), selesai=dmy(r.selesai))
                rows.append(s)

            pdf, filename = open_rml_pdf(path + '/posisi.rml', rows=rows,
                                         company=request.company,
                                         departement=request.session['departemen_nm'],
                                         address=request.address,
                                         alamat=Departemen.query_id(request.session['departemen_id']).first(),
                                         periode='01-01-2017 s.d 31-12-2017')
            return pdf_response(request, pdf, filename)


#########
#  RPT  #
#########
def query_reg(request):
    return PartnerDBSession.query(PartnerDepartemen.id,
                                  PartnerDepartemen.mulai,
                                  PartnerDepartemen.selesai,
                                  Partner.nik.label('nik'),
                                  Partner.nama.label('nama'),
                                  Departemen.nama.label('departemen'),
                                  Jabatan.nama.label('jabatan'), ). \
        join(Partner).join(Departemen). \
        filter(PartnerDepartemen.partner_id == Partner.id,
               PartnerDepartemen.departemen_id == Departemen.id,
               PartnerDepartemen.jabatan_id == Jabatan.id). \
        order_by(PartnerDepartemen.id)


def query_id(request):
    return PartnerDBSession.query(PartnerDepartemen).filter_by(id=request.matchdict['id'])
