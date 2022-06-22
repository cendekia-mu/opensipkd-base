import os
import re

import colander
import transaction
from datatables import (ColumnDT, DataTables, )
from deform import (Form, widget, ValidationFailure, Button, )
# from sqlalchemy.exc import IntegrityErrortpl
from sqlalchemy.exc import IntegrityError

from opensipkd.tools import create_now
from opensipkd.tools.buttons import btn_cancel, btn_save, btn_close, btn_delete, btn_view
from opensipkd.tools.report import open_rml_row, csv_response, open_rml_pdf, pdf_response
from pyramid.httpexceptions import (HTTPFound, HTTPNotFound, )
from pyramid.i18n import TranslationStringFactory
from pyramid.view import view_config
from sqlalchemy import (func, or_, )
from ziggurat_foundations.models.services.user import UserService

from . import BaseView
from .company import company_widget
from .user_login import (
    regenerate_security_code, send_email_security_code, generate_api_key, )
from ..models import (DBSession, User, Group, UserGroup, ResCompany, ExternalIdentity)

_ = TranslationStringFactory('user')


########
# List #
########
class AddSchema(colander.Schema):
    external_user_name = colander.SchemaNode(
        colander.String(), title=_('User Name'))
    provider_name = (colander.SchemaNode(colander.String(), title=_('Provider')))
    local_user_id = (colander.SchemaNode(colander.String(), title=_('User ID')))


class EditSchema(AddSchema):
    external_id = colander.SchemaNode(colander.String(),
                                      widget=widget.TextInputWidget(readonly=True),
                                      missing=colander.drop)


class ListSchema(colander.Schema):
    id = colander.SchemaNode(colander.String())
    external_user_name = colander.SchemaNode(
        colander.String(), title=_('User Name'))
    provider_name = (colander.SchemaNode(colander.String(), title=_('Provider')))
    local_user_id = (colander.SchemaNode(colander.String(), title=_('User ID')))


class UserExt(BaseView):
    def __init__(self, request):
        super(UserExt, self).__init__(request)
        self.edit_schema = EditSchema
        self.list_schema = ListSchema
        # self.list_url = "/user/ext"
        self.list_route = "user-ext"
        self.list_buttons = (btn_view, btn_delete, btn_close)


    @view_config(
        route_name='user-ext', renderer='templates/form_input.pt',
        permission='user-view')
    def view_list(self):
        form = super(UserExt, self).view_list()
        return form

    @view_config(
        route_name='user-ext-view', renderer='templates/form_input.pt',
        permission='user-view')
    def view_view(self):
        return super(UserExt, self).view_view()

    @view_config(
        route_name='user-ext-delete', renderer='templates/form_input.pt',
        permission='user-edit')
    def view_delete(self):
        return super(UserExt, self).view_delete()

    @view_config(
        route_name='user-ext-act', renderer='json', permission='user-view')
    def view_act(self):
        req = self.req
        url_dict = req.matchdict
        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(ExternalIdentity.external_id, mData='id'),
                ColumnDT(ExternalIdentity.external_user_name, mData='external_user_name'),
                ColumnDT(ExternalIdentity.provider_name, mData='provider_name'),
                ColumnDT(ExternalIdentity.local_user_id, mData='local_user_id'),
            ]
            query = DBSession.query().select_from(ExternalIdentity). \
                outerjoin(User, User.id == ExternalIdentity.local_user_id)
            if self.req.user.company_id:
                query = query.filter(User.company_id == self.req.user.company_id)
            row_table = DataTables(req.GET, query, columns)
            return row_table.output_result()

    def delete_msg(self, row):
        return f'Data ID {row.external_id} sudah dihapus.'

    def query_id(self):
        return DBSession.query(ExternalIdentity).filter_by(external_id=self.req.matchdict["id"])
        # elif url_dict['act'] == 'csv':
        #     query = query_register()
        #     row = query.first()
        #     header = row.keys()
        #     rows = []
        #     for item in query.all():
        #         rows.append(list(item))
        #
        #     filename = 'user.csv'
        #     value = {
        #         'header': header,
        #         'rows': rows,
        #     }
        #     return csv_response(request, value, filename)
        # elif url_dict['act'] == 'pdf':
        #     # todo ganti rml jadi openoffice
        #     query = query_register()
        #     _here = os.path.dirname(__file__)  # get current folder -> views
        #     path = os.path.dirname(_here)  # mundur 1 level
        #     path = os.path.join(path, 'reports')
        #     rml_row = open_rml_row(path + '/user.row.rml')
        #     rows = []
        #     for r in query.all():
        #         s = rml_row.format(user_name=r.user_name, email=r.email,
        #                            registered_date=r.registered_date)
        #         rows.append(s)
        #     pdf, filename = open_rml_pdf(path + '/user.rml', rows=rows,
        #                                  company=request.company,
        #                                  departement=request.departement,
        #                                  address=request.address)
        #     return pdf_response(request, pdf, filename)

