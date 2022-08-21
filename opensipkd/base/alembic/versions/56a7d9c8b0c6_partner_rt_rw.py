"""partner_rt_rw

Revision ID: 56a7d9c8b0c6
Revises: 91f07d138fe9
Create Date: 2022-08-21 21:32:37.318361

"""

# revision identifiers, used by Alembic.
revision = '56a7d9c8b0c6'
down_revision = '91f07d138fe9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    context = op.get_context()
    helpers = context.opts['helpers']
    if not helpers.table_has_column('partner', 'rt'):
        op.add_column('partner', sa.Column('rt', sa.String(3)))
    if not helpers.table_has_column('partner', 'rw'):
        op.add_column('partner', sa.Column('rw', sa.String(3)))
    if not helpers.table_has_column('partner', 'tempat_lahir'):
        op.add_column('partner', sa.Column('tempat_lahir', sa.String(128)))
    if not helpers.table_has_column('partner', 'tgl_lahir'):
        op.add_column('partner',
                      sa.Column('tgl_lahir', sa.DateTime(timezone=False)))
    if not helpers.table_has_column('partner', 'jenis_kelamin'):
        op.add_column('partner', sa.Column('jenis_kelamin', sa.String(1)))
    if not helpers.table_has_column('partner', 'gol_darah'):
        op.add_column('partner', sa.Column('gol_darah', sa.String(2)))
    if not helpers.table_has_column('partner', 'agama'):
        op.add_column('partner', sa.Column('agama', sa.String(32)))
    if not helpers.table_has_column('partner', 'perkawinan'):
        op.add_column('partner', sa.Column('perkawinan', sa.String(2)))
    if not helpers.table_has_column('partner', 'pekerjaan'):
        op.add_column('partner', sa.Column('pekerjaan', sa.String(32)))
    if not helpers.table_has_column('partner', 'kewarganegaraan'):
        op.add_column('partner', sa.Column('kewarganegaraan', sa.String(10)))


def downgrade():
    pass
