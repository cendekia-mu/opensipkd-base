"""add_route_type

Revision ID: 23f0ecac4377
Revises: 8ad1f7810384
Create Date: 2020-11-30 23:02:43.713034

"""

# revision identifiers, used by Alembic.
revision = '23f0ecac4377'
down_revision = '8ad1f7810384'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('routes', 'type'):
        op.add_column('routes', sa.Column('type', sa.Integer, default=0))

    if not helpers.table_has_column('routes', 'app_id'):
        op.add_column('routes', sa.Column('app_id', sa.Integer, default=0))

def downgrade():
    pass
