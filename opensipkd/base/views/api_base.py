import datetime
from decimal import Decimal
from . import api_messages
from pyramid.response import Response
from pyramid.exceptions import HTTPNotFound
from opensipkd.base.models import DBSession



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


    def filter_ids(self, query):
        ids = self.id.split(".")
        filters = dict(zip(self.pkey, ids))
        return query.filter_by(**filters)
    
    def get_orders(self, query):
        if not self.orders:
            self.orders = self.pkey
        for k in self.orders:
            query = query.order_by(getattr(self.table,k))
        return query
    
    def query(self, **kw):
        table = kw.get("table", self.table)
        filter_ids = kw.get("filters", self.filter_ids)
        orders = kw.get("orders", self.get_orders)
        query = self.db_session.query(table)
        if self.id:
            query = filter_ids(query)
        else:
            query = orders(query)
            query = query.limit(self.psize).offset(
                (self.page - 1) * self.psize)

        return query
    
    def success(self, data=[], msg=None):
        result = dict(api_messages.SUCCESS)
        result["data"] = data
        result["error"]["msg"] = msg if msg else "Success"
        return result
    
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
