"""add_route_creted

Revision ID: da566162d3fb
Revises: c35162ddf851
Create Date: 2020-11-30 22:28:10.604024

"""

# revision identifiers, used by Alembic.
revision = 'da566162d3fb'
down_revision = 'c35162ddf851'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('routes', 'created'):
        op.add_column('routes', sa.Column('created', sa.DateTime, default=0))


def downgrade():
    pass
