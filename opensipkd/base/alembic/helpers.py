# http://www.derstappen-it.de/tech-blog/sqlalchemie-alembic-check-if-table-has-column

from alembic import op
from sqlalchemy.engine import reflection


def table_has_column(table, column):
    engine = op.get_bind()
    insp = reflection.Inspector.from_engine(engine)
    has_column = False
    for col in insp.get_columns(table):
        if column not in col['name']:
            continue
        has_column = True
    return has_column
