# http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column

from alembic import op
from sqlalchemy.engine import reflection
import sqlalchemy as sa

def has_table(table, schema=None, insp=None):
    if not insp:
        engine = op.get_bind()
        insp = reflection.Inspector.from_engine(engine)
    return insp.has_table(table, schema=schema)


def table_has_column(table, column, schema=None):
    engine = op.get_bind()
    insp = reflection.Inspector.from_engine(engine)
    has_column = False

    if has_table(table, schema, insp):
        for col in insp.get_columns(table, schema=schema):
            if column != col['name']:
                continue
            has_column = True
    return has_column


def fields_update(table, field, typ, schema="pad"):
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column(table, field, schema):
        op.add_column(table,
                      sa.Column(field, typ), schema=schema)