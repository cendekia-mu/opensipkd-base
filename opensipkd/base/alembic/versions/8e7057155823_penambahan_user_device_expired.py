"""penambahan user device expired

Revision ID: 8e7057155823
Revises: 86c1b4a1da16
Create Date: 2022-07-08 14:58:39.378811

"""

# revision identifiers, used by Alembic.
revision = '8e7057155823'
down_revision = '86c1b4a1da16'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('user_device', 'expired'):
        op.add_column('user_device', sa.Column('expired', sa.DateTime(timezone=True)))

    op.alter_column('user_device', sa.Column('expired', sa.DateTime(timezone=True)))

    if not helpers.table_has_column('routes', 'create_uid'):
        op.add_column('routes', sa.Column('create_uid', sa.Integer, default=0))

    if not helpers.table_has_column('routes', 'update_uid'):
        op.add_column('routes', sa.Column('update_uid', sa.Integer, default=0))


def downgrade():
    pass
