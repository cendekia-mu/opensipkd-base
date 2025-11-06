from datetime import datetime, date
import logging
from decimal import Decimal
from deform import Form, ValidationFailure
from pyramid.response import Response
from pyramid.exceptions import HTTPNotFound, HTTPBadRequest
from opensipkd.base.models import DBSession
from opensipkd.tools.buttons import btn_save, btn_cancel
from opensipkd.base.views.common import DataTables, ColumnDT
from deform.widget import SelectWidget
import colander
from . import api_messages
from ..tools import obj2json

from pyramid.response import Response

from pyramid_restful.views import APIView
import json
_log = logging.getLogger(__name__)


class ApiViews(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.req = kwargs.get("request", None)
        self.db_session = DBSession
        self.buttons = (btn_save, btn_cancel)
        self.table = None
        self.pkey = ("id",)
        self.orders = None
        self.bindings = {}
        self.id = -1
        self.autocomplete = True
        self.form_widget = None
        self.columns = None
        self.list_schema = None
        self.add_schema = None
        self.edit_schema = None
        self.psize = 25

        self.page = 1

    def list_join(self, query, **kw):
        return query

    def list_filter(self, query, **kw):
        return query

    def get_list(self, **kwargs):
        """
        parameter
        list_schema optional
        list_join callback
        list_filter callback
        """
        url = []
        select_list = {}
        list_schema = kwargs.get("list_schema")
        if not list_schema:
            list_schema = self.list_schema and self.list_schema or None

        if not self.columns:
            columns = []
            for d in list_schema():
                global_search = True
                search_method = hasattr(d, "search_method") \
                    and getattr(d, "search_method") or "string_contains"
                if hasattr(d, "global_search"):
                    if d.global_search == False:
                        global_search = False

                if hasattr(d, "field"):
                    if type(d.field) == str:
                        columns.append(
                            ColumnDT(getattr(self.table, d.field),
                                     mData=d.name,
                                     global_search=global_search,
                                     search_method=search_method))
                    else:
                        columns.append(
                            ColumnDT(d.field, mData=d.name,
                                     global_search=global_search,
                                     search_method=search_method
                                     ))
                else:
                    columns.append(
                        ColumnDT(getattr(self.table, d.name),
                                 mData=d.name,
                                 global_search=global_search,
                                 search_method=search_method))
                if hasattr(d, "widget"):
                    if d.widget:
                        _log.debug(d.widget)
                        if type(d.widget) is SelectWidget:
                            select_list[d.name] = d.widget.values

                if hasattr(d, "url"):
                    url.append(d.name)
        else:
            columns = self.columns

        query = self.db_session.query().select_from(self.table)
        list_join = kwargs.get('list_join')
        if list_join is not None:
            query = list_join(query, **kwargs)
        else:
            query = self.list_join(query, **kwargs)
        if self.req.user and self.req.user.company_id and hasattr(self.table, "company_id"):
            query = query.filter(
                self.table.company_id == self.req.user.company_id)
        list_filter = kwargs.get('list_filter')
        if list_filter is not None:
            query = list_filter(query, **kwargs)
        else:
            query = self.list_filter(query, **kwargs)

        # log.debug(str(columns))
        # qry = query.add_columns(*[c.sqla_expr for c in columns])
        # log.debug(str(qry))
        row_table = DataTables(self.req.GET, query, columns)
        result = row_table.output_result()
        data = result and result.get("data") or {}
        for res in data:
            for k in res:
                if k in select_list.keys():
                    vals = select_list[k]
                    for r in vals:
                        if r and str(r) == str(res[k]):
                            res[k] = vals[r]
        #     for k, v in d.items():
        #         if k in url and v:
        #             link = "/".join([self.home, nik_url, v])
        #             d[k] =f'<a href="{link}" target="_blank">View</a>'
        if result.get("error"):
            _log.error(result.get("error"))
            # _log.error(str(result))
        return result

    def not_found(self, msg=None):
        if not msg:
            msg = api_messages.NOT_FOUND
        return Response(json=msg, status=404)

    def obj2json(self, obj):
        return obj2json(obj)

    def get_bindings(self, row=None):
        """Get form bindings for the specified row."""
        return {}

    def form_validator(self, form, controls):
        """Get Validator Form"""

    def form_validate(self, form, controls):
        """Validate form"""
        try:
            data = form.validate(controls)
            return data
        except ValidationFailure as e:
            raise HTTPBadRequest(explanation=str(e.error.asdict()))
        
        return dict(data)
    
    def get_form(self, class_form, row=None, buttons=(btn_save, btn_cancel),
                 **kwargs):
        buttons = self.buttons and self.buttons or buttons
        if "bindings" in kwargs and kwargs["bindings"]:
            bindings = kwargs["bindings"]
        elif self.bindings:
            bindings = self.bindings
        else:
            bindings = self.get_bindings(row)

        form_params = {}

        if "validator" in kwargs and kwargs["validator"]:
            form_params["validator"] = kwargs["validator"]
        else:
            form_params["validator"] = self.form_validator

        if "after_bind" in kwargs and kwargs["after_bind"]:
            form_params["after_bind"] = kwargs["after_bind"]

        if self.form_widget:
            form_params["widget"] = self.form_widget

        schema = class_form(**form_params)
        schema = schema.bind(request=self.req, **bindings)
        schema.request= self.req
        if row:
            schema.deserialize(row)

        return Form(schema, buttons=buttons, autocomplete=self.autocomplete)

    # def get_filters(self, query, **kw):
    #     return query

    # def get_orders(self, query, **kw):
    #     table = kw.get("table", self.table)
    #     if not self.orders:
    #         self.orders = self.pkey

    #     query = query.order_by(*(getattr(table, k) for k in self.orders))
    #     return query

    # def get_joins(self, query, **kw):
    #     return query

    # def get_groups(self, query, **kw):
    #     return query

    # def query(self, **kw):
    #     self.psize = int(self.req.params.get("size", 25))
    #     self.page = int(self.req.params.get("page", 1))

    #     table = kw.get("table", self.table)
    #     get_filters = kw.get("filters", self.get_filters)
    #     get_joins = kw.get("joins", self.get_joins)
    #     get_groups = kw.get("groups", self.get_groups)
    #     get_orders = kw.get("orders", self.get_orders)
    #     query = self.db_session.query(table)
    #     query = get_joins(query,  **kw)
    #     query = get_groups(query,  **kw)
    #     query = get_filters(query, **kw)
    #     query = get_orders(query, **kw)
    #     query = query.limit(self.psize).offset((self.page - 1) * self.psize)
    #     return query

    # def query_id(self, **kw):
    #     table = kw.get("table", self.table)
    #     get_joins = kw.get("joins", self.get_joins)
    #     get_groups = kw.get("groups", self.get_groups)
    #     get_filters = kw.get("filters", self.get_filters)
    #     get_orders = kw.get("orders", self.get_orders)
    #     if hasattr(table, "query_id") and self.id:
    #         query = table.query_id(self.id)
    #         query = get_joins(query, **kw)
    #         query = get_groups(query, **kw)
    #         query = get_filters(query, **kw)
    #         query = get_orders(query, **kw)
    #         return query

    #     return self.query(**kw)

    def json_adapter(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, colander._null):
            return None
        else:
            return obj

    def success(self, data, msg=None):
        """
        Mengubah data menjadi list dan convert objek menjadi string
        """
        if not isinstance(data, list):
            data = [data]
        for i, item in enumerate(data):
            data[i] = self.obj2json(item)
        data = {"data": data}
        if msg:
            data.update(msg)
        return data

    # def get(self, self.req. *args, **kwargs):
        # self.req = request
        # query=self.query()
        # if not query.first():
        #     return HTTPNotFound()
        # data = []
        # for row in query:
        #     d = dict(row.__dict__)
        #     d.pop('_sa_instance_state', None)
        #     for key, value in d.items():
        #         if isinstance(value, datetime.datetime):
        #             d[key] = value.isoformat()
        #         elif isinstance(value, Decimal):
        #             d[key] = float(value)
        #     data.append(d)
        # return Response(json=self.success(data=data))
    def _get(self, request, *args, **kwargs):
        self.req = request
        if "draw" not in self.req.params:
            self.req.GET.add('draw', "1")
        if "length" not in self.req.params:
            self.req.GET.add('length', "10")
        if "start" not in self.req.params:
            self.req.GET.add('start', "0")
        # rec_id = self.req.matchdict.get('id')
        # if rec_id:
        #     self.req.GET.add('columns[0][search][value]', rec_id)
        return self.get_list(**kwargs)
    
    def get_custom_render(self, data):
        return data
    
    def get(self, request, *args, **kwargs):
        d = self._get(request, *args, **kwargs)
        d = self.get_custom_render(d)
        return Response(json=json.loads(json.dumps(d, default=self.json_adapter)))

    def post(self, request, *args, **kwargs):
        self.req = request
        return self.req

    def delete(self):
        query = self.db_session.query(self.table)
        # query = self.filter_ids(query)
        row = query.first()
        if not row:
            return HTTPNotFound()

        return Response(json=self.success())

    def put(self, data):
        self.req = data
        return self.req

    def patch(self, data):
        self.req = data
        return self.req

    def save(self, data, user=None, obj=None):
        if not user:
            user = self.req.session.user
        if not obj:
            obj = self.table()
            obj.create_date = datetime.now()
            obj.create_uid = user and user.id or None
            obj.enabled = 1
        else:
            obj.write_date = datetime.now()
            obj.write_uid = user and user.id or None

        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        self.db_session.add(obj)
        self.db_session.flush()
        return obj
