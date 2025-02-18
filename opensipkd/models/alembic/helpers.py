# http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection


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
    else:
        has_column = True
    return has_column


def table_has_seq(table, name, schema=None):
    engine = op.get_bind()
    insp = reflection.Inspector.from_engine(engine)
    has_seq = False

    if has_table(table, schema, insp):
        for seq in insp.get_sequence_names(schema=schema):
            if name != seq:
                continue
            has_seq = True
    else:
        has_seq = True
    return has_seq


def fields_update(table, field, typ, schema=None, **kw):
    context = op.get_context()
    # helpers = context.opts['helpers']
    # if not helpers.table_has_column(table, field, schema):
    if not table_has_column(table, field, schema):
        op.add_column(table, sa.Column(field, typ), schema=schema)
        nullable = kw.get("nullable", None)
        if nullable != None and nullable == False:
            default = kw.get("default")
            if default != None:
                op.execute(
                    f"UPDATE {schema}.{table} SET {field} = {default}")
                op.alter_column(table, field, nullable=False, schema=schema)


def seq_update(table, seq, schema=None, *args):
    # seq_name = "pad_spt_type_id_seq"
    # table_nm = "pad_spt_type"
    if not table_has_seq(table, seq, schema):
        statement = f"CREATE SEQUENCE {schema}.{seq} START WITH 1"
        op.execute(statement)
        statement = f"SELECT setval('{schema}.{seq}', (SELECT MAX(id) FROM {schema}.{table}))"
        op.execute(statement)
        statement = f"alter table {schema}.{table} alter column id set default nextval('{schema}.{seq}')"
        op.execute(statement)
