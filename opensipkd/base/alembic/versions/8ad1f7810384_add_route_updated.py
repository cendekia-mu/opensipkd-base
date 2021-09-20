"""add_route_updated

Revision ID: 8ad1f7810384
Revises: da566162d3fb
Create Date: 2020-11-30 22:58:34.288664

"""

# revision identifiers, used by Alembic.
revision = '8ad1f7810384'
down_revision = 'da566162d3fb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('routes', 'updated'):
        op.add_column('routes', sa.Column('updated', sa.DateTime, default=0))

    if not helpers.table_has_column('routes', 'create_uid'):
        op.add_column('routes', sa.Column('create_uid', sa.Integer, default=0))

    if not helpers.table_has_column('routes', 'update_uid'):
        op.add_column('routes', sa.Column('update_uid', sa.Integer, default=0))

def downgrade():
    pass
