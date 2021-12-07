"""add partner_id to user

Revision ID: 37ca8f816946
Revises: 72dd62d47460
Create Date: 2021-12-01 16:28:19.147741

"""

# revision identifiers, used by Alembic.
revision = '37ca8f816946'
down_revision = '72dd62d47460'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('users', 'partner_id'):
        op.add_column('users', sa.Column('partner_id', sa.Integer))


def downgrade():
    pass
