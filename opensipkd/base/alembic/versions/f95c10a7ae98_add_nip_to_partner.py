"""Add nip to partner

Revision ID: f95c10a7ae98
Revises: 56a7d9c8b0c6
Create Date: 2022-08-22 18:17:00.798094

"""

# revision identifiers, used by Alembic.
revision = 'f95c10a7ae98'
down_revision = '56a7d9c8b0c6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('partner', 'nip'):
        op.add_column('partner', sa.Column('nip', sa.String(32)))

    if not helpers.table_has_column('partner', 'npwp'):
        op.add_column('partner', sa.Column('npwp', sa.String(32)))



def downgrade():
    pass
