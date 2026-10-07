# http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection
from sqlalchemy.sql.schema import Column
from typing import Any


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


def fields_update(table, field, typ, schema="public"):
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column(table, field, schema):
        op.add_column(table,
                      sa.Column(field, typ), schema=schema)


def add_column(table_name: str,
    column: Column[Any],
    *,
    schema: str | None = None,
    if_not_exists: bool | None = None,
    inline_references: bool | None = None,
    inline_primary_key: bool | None = None,) -> None:
    if not table_has_column(table_name, column.name, schema=schema):
            op.add_column(table_name,
                column,
                schema= schema,
                if_not_exists= if_not_exists,
                inline_references= inline_references,
                inline_primary_key= inline_primary_key,
            ) 