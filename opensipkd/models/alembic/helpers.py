# http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

def get_insp():
    engine = op.get_bind()
    return reflection.Inspector.from_engine(engine)

def create_table(*args, **kw):
    table_name= args[0]
    if not has_table(table_name, kw.get("schema"), kw.get("insp")):
        kw.pop("insp", None)
        op.create_table(*args, **kw)

def add_column(*args, **kw):
    table_name= args[0]
    col_name= args[1].name
    if not table_has_column(table_name, col_name, **kw):
        kw.pop("insp", None)
        op.add_column(*args, **kw)
        
def has_table(table, schema=None, insp=None):
    if not insp:
        engine = op.get_bind()
        insp = reflection.Inspector.from_engine(engine)
    return insp.has_table(table, schema=schema)


def table_has_column(table, column, schema=None, insp=None):
    if not insp:
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

def create_unique_constraint(*args, **kw):
    const_name = args[0]
    if const_name:
        table_name = args[1]
        existing_constraints = kw["insp"].get_unique_constraints(table_name, schema=kw["schema"])
        constraint_names = [c['name'] for c in existing_constraints]
        if const_name not in constraint_names:
            kw.pop("insp", None)
            op.create_unique_constraint(*args, **kw)
        else:
            print(f"Skipping: {const_name} already exists.")
    else:
        raise Exception(f"{const_name} Wajib ada")

def create_index(*args, **kw):
    idx_name = args[0]
    if idx_name:
        table_name = args[1]
        existing_names = kw["insp"].get_indexes(table_name, schema=kw["schema"])
        existings = [c['name'] for c in existing_names]
        if idx_name not in existings:
            kw.pop("insp", None)
            op.create_index(*args, **kw)
        else:
            print(f"Skipping: {idx_name} already exists.")
    else:
        raise Exception(f"{idx_name} Wajib ada")

    
def fields_update(table, field, typ,  schema="pad", **kw):
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column(table, field, schema):
        op.add_column(table, sa.Column(field, typ), schema=schema)
        nullable = kw.get("nullable", None)
        if nullable != None and nullable == False:
            default = kw.get("default")
            if default != None:
                op.execute(
                    f"UPDATE {schema}.{table} SET {field} = {default}")
                op.alter_column(table, field, nullable=False, schema=schema)
