import os
from datetime import datetime

from pyramid.view import (
    view_config,
)

from ..models import DBSession
from ..models import (Partner, Departemen,
                      )
from opensipkd.tools.report import (
    open_rml_row,
    open_rml_pdf,
    pdf_response,
    csv_response,
)
from ..views import (BaseView, )


class ViewRpt(BaseView):
    @view_config(route_name='partner-rpt', renderer='csv')
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

            filename = 'partner.csv'
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
            rml_row = open_rml_row(path + '/partner.row.rml')

            rows = []
            for r in query.all():
                s = rml_row.format(kode=r.kode, nama=r.nama, vendor=r.is_vendor and "Ya" or "-",
                                   is_customer=r.is_customer and "Ya" or "-",
                                   status=r.status and "Aktif" or "Pasif")
                rows.append(s)

            pdf, filename = open_rml_pdf(path + '/partner.rml', rows=rows,
                                         company=request.company,
                                         departement=request.departement,
                                         alamat=Departemen.query_id(request.session['departemen_id']).first().alamat, )
            return pdf_response(request, pdf, filename)


# ##########
# # query   #
# ##########    

def query_reg(request):
    return DBSession.query(Partner.kode,
                           Partner.nama,
                           Partner.is_vendor,
                           Partner.is_customer,
                           Partner.status, ). \
        filter(Partner.status == 1). \
        order_by(Partner.id)
