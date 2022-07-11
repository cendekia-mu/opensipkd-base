"""tambah idcard

Revision ID: 91f07d138fe9
Revises: 8e7057155823
Create Date: 2022-07-11 18:29:13.867835

"""

# revision identifiers, used by Alembic.
revision = '91f07d138fe9'
down_revision = '8e7057155823'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('partner', 'idcard'):
        op.add_column('partner',
                      sa.Column('idcard', sa.String(256)))


def downgrade():
    pass
