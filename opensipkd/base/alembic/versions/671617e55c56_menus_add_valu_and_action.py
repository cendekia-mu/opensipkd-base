"""menus add valu and action

Revision ID: 671617e55c56
Revises: f95c10a7ae98
Create Date: 2022-12-27 17:59:55.766347

"""

# revision identifiers, used by Alembic.
revision = '671617e55c56'
down_revision = 'f95c10a7ae98'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('menus', 'valu'):
        op.add_column('menus',
                      sa.Column('valu', sa.String(256)))

    if not helpers.table_has_column('menus', 'meth'):
        op.add_column('menus',
                      sa.Column('meth', sa.String(256)))
    if not helpers.table_has_column('menus', 'page_typ'):
        op.add_column('menus',
                      sa.Column('page_typ', sa.String(256)))


        
def downgrade():
    pass
