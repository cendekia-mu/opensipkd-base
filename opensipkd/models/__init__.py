from sqlalchemy import event

from .base import *
from .common import *
from .users import *
from .wilayah import *
from .partner import *
from .departemen import *
from .pegawai import *

# from .meta import *
# from .targets import *
# from .wilayah import *
def has_permission(action):
    pass

@event.listens_for(User, 'before_delete', has_permission('delete'))
def receive_before_delete(mapper, connection, target):
    "listen for the 'before_delete' event"
    # ... (event handling logic) ...
    pass

ALL_TABLES = {}
for sub_class in Base.__subclasses__():
    if hasattr(sub_class, "__tablename__"):
        tablename = sub_class.__tablename__
        if tablename not in ALL_TABLES:
            ALL_TABLES.update({tablename: sub_class})


def query_table(table_name, fields=None, domain=None):
    cls = ALL_TABLES[table_name]
    if fields:
        query = DBSession.query().select_from(cls)
        # for field in fields:
        query = query.add_columns(*[getattr(cls, c) for c in fields])
    else:
        query = DBSession.query(cls)

    if domain:
        filter_expressions = []
        for d in domain:
            field = getattr(cls, d[0])
            operator = d[1]
            value = d[2]
            filter_expressions.append(field.op(operator)(value))
        query = query.filter(
            *[
                e for i, e in enumerate(filter_expressions)
                if e is not None]
        )
    return query
