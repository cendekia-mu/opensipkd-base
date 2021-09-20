"""change_route_status_null

Revision ID: 72dd62d47460
Revises: 23f0ecac4377
Create Date: 2020-11-30 23:08:14.118795

"""

# revision identifiers, used by Alembic.
revision = '72dd62d47460'
down_revision = '23f0ecac4377'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass
    # op.alter_column('routes', 'status', nullable=False)

def downgrade():
    pass
