"""add rpc* to partner

Revision ID: e7ce8fb3cbed
Revises: 
Create Date: 2025-12-03 22:36:33.826902

"""

# revision identifiers, used by Alembic.
revision = 'e7ce8fb3cbed'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('partner', 'rpc_url'):
        op.add_column('partner',
                      sa.Column('rpc_url', sa.String(length=50)),
                      schema='public')
    if not helpers.table_has_column('partner', 'rpc_user'):
        op.add_column('partner',
                      sa.Column('rpc_user', sa.String(length=50)),
                      schema='public')
    if not helpers.table_has_column('partner', 'rpc_callback'):
        op.add_column('partner',
                      sa.Column('rpc_callback', sa.String(length=255)),
                      schema='public')
    if not helpers.table_has_column('partner', 'rpc_password'):
        op.add_column('partner',
                      sa.Column('rpc_password', sa.String(length=50)),
                      schema='public')
        



def downgrade():
    pass
