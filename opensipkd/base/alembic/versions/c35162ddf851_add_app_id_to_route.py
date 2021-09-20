"""add app_id to route

Revision ID: c35162ddf851
Revises: e628a2dc0b23
Create Date: 2020-11-23 14:41:33.244797

"""

# revision identifiers, used by Alembic.
revision = 'c35162ddf851'
down_revision = 'e628a2dc0b23'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('routes', 'app_id'):
        op.add_column('routes', sa.Column('app_id', sa.SmallInteger, default=0))


def downgrade():
    pass
