"""add users api_key

Revision ID: e628a2dc0b23
Revises: 35f453a443
Create Date: 2018-12-10 19:29:52.211689

"""

# revision identifiers, used by Alembic.
revision = 'e628a2dc0b23'
down_revision = '35f453a443'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('users', 'api_key'):
        op.add_column('users', sa.Column('api_key', sa.String(256)))


def downgrade():
    pass
