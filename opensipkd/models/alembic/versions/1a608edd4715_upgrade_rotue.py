"""ugrade routes

Revision ID: 1a608edd4715
Revises: 
Create Date: 2024-11-16 09:06:29.860302

"""

# revision identifiers, used by Alembic.
revision = '1a608edd4715'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    schema = "public"
    context = op.get_context()
    helpers = context.opts['helpers']
    helpers.fields_update("routes", "module", sa.String(256), schema)
    helpers.fields_update("routes", "is_menu", sa.SmallInteger, schema)
    helpers.fields_update("routes", "parent_id", sa.Integer, schema)
    helpers.fields_update("routes", "order_id", sa.Integer, schema)
    helpers.fields_update("routes", "permission", sa.String(256), schema)
    helpers.fields_update("routes", "class_view", sa.String(256), schema)
    helpers.fields_update("routes", "def_func", sa.String(256), schema)
    helpers.fields_update("routes", "template", sa.String(256), schema)
    helpers.fields_update("routes", "icon", sa.String(256), schema)


def downgrade():
    pass