import os
from datetime import datetime

from opensipkd.tools.report import (
    open_rml_row,
    open_rml_pdf,
    pdf_response,
    csv_response,
)
from pyramid.view import (
    view_config,
)

from ..models import DBSession
from ..models import (
    Jabatan,
    Departemen,
)
from ..views import (BaseView, )


class view_rpt(BaseView):
    @view_config(route_name='jabatan-rpt', renderer='csv')
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

            filename = 'jabatan.csv'
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
            rml_row = open_rml_row(path + '/jabatan.row.rml')

            rows = []
            for r in query.all():
                s = rml_row.format(kode=r.kode, nama=r.nama, status=r.status and "Aktif" or "Pasif")
                rows.append(s)

            pdf, filename = open_rml_pdf(path + '/jabatan.rml', rows=rows,
                                         company=request.company,
                                         departement=request.session['departemen_nm'],
                                         address=request.address,
                                         alamat=Departemen.query_id(request.session['departemen_id']).first(),
                                         periode='01-01-2017 s.d 31-12-2017')
            return pdf_response(request, pdf, filename)


# ##########
# # query   #
# ##########    

def query_reg(request):
    return DBSession.query(Jabatan.kode,
                           Jabatan.nama,
                           Jabatan.status, ). \
        filter(Jabatan.status == 1). \
        order_by(Jabatan.id)
