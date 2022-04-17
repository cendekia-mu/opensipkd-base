"""Add Wilayah to Partner

Revision ID: 86c1b4a1da16
Revises: 044041bb09ef
Create Date: 2022-04-14 23:50:08.268569

"""

# revision identifiers, used by Alembic.
revision = '86c1b4a1da16'
down_revision = '044041bb09ef'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('partner', 'provinsi_id'):
        op.add_column('partner', sa.Column('provinsi_id', sa.Integer,  default=0))

    if not helpers.table_has_column('partner', 'dati2_id'):
        op.add_column('partner', sa.Column('dati2_id', sa.Integer, default=0))

    if not helpers.table_has_column('partner', 'kecamatan_id'):
        op.add_column('partner', sa.Column('kecamatan_id', sa.Integer, default=0))

    if not helpers.table_has_column('partner', 'desa_id'):
        op.add_column('partner', sa.Column('desa_id', sa.Integer, default=0))

    if not helpers.table_has_column('partner', 'company_id'):
        op.add_column('partner', sa.Column('company_id', sa.Integer, default=0))

def downgrade():
    pass
