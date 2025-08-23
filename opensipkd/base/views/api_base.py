import datetime
from decimal import Decimal
from deform import Form
from pyramid.response import Response
from pyramid.exceptions import HTTPNotFound
from opensipkd.base.models import DBSession
from opensipkd.tools.pbb import FixSppt
from opensipkd.tools.buttons import btn_save, btn_cancel
from . import api_messages
from ..tools import obj2json


class ApiViews:
    def __init__(self, request):
        self.request = request
        self.id = self.request.matchdict.get("id")
        self.db_session = DBSession
        self.table = None
        self.pkey = ("id")
        self.orders = None
        self.psize = int(request.params.get("size", 25))
        self.page = int(request.params.get("page", 1))
        self.buttons = (btn_save, btn_cancel)
        self.bindings = {}
        self.form_widget = None
        self.autocomplete = True

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

    def filter_ids(self, query, **kw):
        # table = kw.get("table", self.table)
        ids = FixSppt(self.id).row_dotted.split(".")
        filters = dict(zip(self.pkey, ids))
        return query.filter_by(**filters)

    def get_orders(self, query, **kw):
        table = kw.get("table", self.table)
        if not self.orders:
            self.orders = self.pkey
        
        query = query.order_by(*(getattr(table, k) for k in self.orders))
        return query
    
    def query(self, **kw):
        table = kw.get("table", self.table)
        filter_ids = kw.get("filters", self.filter_ids)
        orders = kw.get("orders", self.get_orders)
        query = self.db_session.query(table)
        if self.id:
            query = filter_ids(query, table=table)
        else:
            query = orders(query, table=table)
            query = query.limit(self.psize).offset(
                (self.page - 1) * self.psize)

        return query
    
    def success(self, data=[], msg=None):
        if type(data) is not list:
            data = [data]
        for i, item in enumerate(data):
            data[i] = self.obj2json(item)
        data = {"data": data}
        if msg:
            data.update(msg)
        return data
    
    def get(self):
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

    def post(self, data):
        self.request = data
        return self.request

    def delete(self):
        query = self.db_session.query(self.table)
        query = self.filter_ids(query)
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
