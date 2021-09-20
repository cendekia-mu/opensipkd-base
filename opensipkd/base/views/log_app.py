import json

import colander
from datatables import ColumnDT
from deform import Form, widget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from opensipkd.base import DBSession
from opensipkd.base.models.handlers import Log
from opensipkd.base.views import BaseView, DataTables


class AddSchema(colander.Schema):
    created_at = colander.SchemaNode(
        colander.DateTime())
    logger = colander.SchemaNode(
        colander.String())
    level = colander.SchemaNode(
        colander.String())
    trace = colander.SchemaNode(
        colander.String(),
        missing=colander.drop)
    msg = colander.SchemaNode(
        colander.String(),
        widget=widget.TextAreaWidget(rows=10,),
        missing=colander.drop)


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
                             missing=colander.drop,
                             widget=widget.HiddenWidget(),
                             )


class Views(BaseView):
    @view_config(route_name='log', renderer='templates/list.pt',
                 permission='log')
    def view_list(self):
        url = "log"
        cols = [
            {'title': "ID", 'data': "id"},
            {'title': "Date/Time", 'data': "created_at", 'width': "150"},
            {'title': "Logger", 'data': "logger", 'width': "50"},
            # {'title': "Trace", 'data': "trace", 'width': "50"},
            {'title': "Level", 'data': "level", 'width': "50"},
            {'title': "Message", 'data': "msg"},
        ]

        col_defs = [{
            "searchable": False,
            "visible": False,
            "targets": [0]
        }]
        buttons = "btn_view"
        return dict(cols=cols, url=url, col_defs=json.dumps(col_defs),
                    buttons=buttons)

    ##########
    # Action #
    ##########
    @view_config(route_name='log-act', renderer='json_rpc',
                 permission='log')
    def view_act(self):
        request = self.req
        url_dict = request.matchdict
        if url_dict['act'] == 'grid':
            columns = [
                ColumnDT(Log.id, mData='id'),
                ColumnDT(Log.logger, mData='logger'),
                ColumnDT(Log.level, mData='level'),
                # ColumnDT(Log.trace, mData='trace'),
                ColumnDT(Log.msg, mData='msg'),
                ColumnDT(Log.created_at, mData='created_at', search_method='date'),
            ]
            query = DBSession.query().select_from(Log)
            rowTable = DataTables(request.GET, query, columns)
            return rowTable.output_result()

    @view_config(route_name='log-view', renderer='templates/form_input.pt',
                 permission='log')
    def view_view(self):
        request = self.req
        q = self.query_id()
        row = q.first()
        if not row:
            return self.id_not_found()
        form = self.get_form(EditSchema, buttons=("Tutup",))
        if request.POST:
            return self.route_list()

        values = row.to_dict()
        form.set_appstruct(values)
        return dict(form=form.render(readonly=True), scripts="")

    def query_id(self):
        request = self.req
        return DBSession.query(Log).filter_by(id=request.matchdict['id'])

    def id_not_found(self):
        request = self.req
        msg = 'BillerModel ID %s Tidak Ditemukan.' % request.matchdict['id']
        request.session.flash(msg, 'error')
        return self.route_list()

    def route_list(self):
        request = self.req
        return HTTPFound(location=request.route_url('log'))

    def get_form(self, class_form, row=None, buttons=('simpan', 'batal')):
        request = self.req
        schema = class_form(validator=self.form_validator)
        schema = schema.bind()
        schema.request = request
        if row:
            schema.deserialize(row)
        return Form(schema, buttons=buttons)

    def form_validator(self, form, value):
        pass
