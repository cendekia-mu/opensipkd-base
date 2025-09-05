import datetime
from decimal import Decimal
from deform import Form
from pyramid.response import Response
from pyramid.exceptions import HTTPNotFound
from opensipkd.base.models import DBSession
from opensipkd.tools.buttons import btn_save, btn_cancel
from . import api_messages
from ..tools import obj2json

from pyramid.response import Response

from pyramid_restful.views import APIView


class ApiViews(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request = kwargs.get("request", None)
        self.db_session = DBSession
        self.buttons = (btn_save, btn_cancel)
        self.table = None
        self.pkey = ("id")
        self.orders = None
        self.bindings = {}
        self.id = -1
        self.autocomplete = True
        self.form_widget = None


        self.psize = 25


        self.page =1
        
    # def __init__(self, request):
    #     self.request = request
    #     self.id = self.request.matchdict.get("id")

    def obj2json(self, obj):
        return obj2json(obj)
    
    def get_bindings(self, row=None):
        """Get form bindings for the specified row."""
        return {}

    def form_validator(self, form, controls):
        """Get Validator Form"""

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
        schema = schema.bind(request=self.request, **bindings)
        schema.request = self.request
        if row:
            schema.deserialize(row)

        return Form(schema, buttons=buttons, autocomplete=self.autocomplete)

    def get_filters(self, query, **kw):
        return query

    def get_orders(self, query, **kw):
        table = kw.get("table", self.table)
        if not self.orders:
            self.orders = self.pkey
        
        query = query.order_by(*(getattr(table, k) for k in self.orders))
        return query
    
    def get_joins(self, query, **kw):
        return query
    
    def get_groups(self, query, **kw):
        return query
    
    def query(self, **kw):
        self.psize = int(self.request.params.get("size", 25))
        self.page = int(self.request.params.get("page", 1))

        table = kw.get("table", self.table)
        get_filters = kw.get("filters", self.get_filters)
        get_joins = kw.get("joins", self.get_joins)
        get_groups = kw.get("groups", self.get_groups)
        get_orders = kw.get("orders", self.get_orders)
        query = self.db_session.query(table)
        query = get_joins(query,  **kw)
        query = get_groups(query,  **kw)
        query = get_filters(query, **kw)
        query = get_orders(query, **kw)
        query = query.limit(self.psize).offset((self.page - 1) * self.psize)
        return query
    
    def query_id(self, **kw):
        table = kw.get("table", self.table)
        get_joins = kw.get("joins", self.get_joins)
        get_groups = kw.get("groups", self.get_groups)
        get_filters = kw.get("filters", self.get_filters)
        get_orders = kw.get("orders", self.get_orders)
        if hasattr(table, "query_id") and self.id:
            query = table.query_id(self.id)
            query = get_joins(query, **kw)
            query = get_groups(query, **kw)
            query = get_filters(query, **kw)
            query = get_orders(query, **kw)
            return query

        return self.query(**kw)
    
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
    
    def get(self, request, *args, **kwargs):
        self.request = request
        query=self.query()
        if not query.first():
            return HTTPNotFound()
        data = []
        for row in query:
            d = dict(row.__dict__)
            d.pop('_sa_instance_state', None)
            for key, value in d.items():
                if isinstance(value, datetime.datetime):
                    d[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    d[key] = float(value)
            data.append(d)
        return Response(json=self.success(data=data))

    def post(self, request, *args, **kwargs):
        self.request = request
        return self.request

    def delete(self):
        query = self.db_session.query(self.table)
        # query = self.filter_ids(query)
        row = query.first()
        if not row:
            return HTTPNotFound()


        return Response(json=self.success())

    def put(self, data):
        self.request = data
        return self.request

    def patch(self, data):
        self.request = data
        return self.request
