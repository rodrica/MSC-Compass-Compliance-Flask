"""Update reports to BaseModel structure

Revision ID: f4a1fa3c2b9d
Revises: 
Create Date: 2022-02-17 14:34:59.538319

"""
from alembic import op
from jinja2 import defaults
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f4a1fa3c2b9d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("reports", "public") as t:
        t.add_column(sa.Column("description", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("tags", postgresql.JSONB, nullable=True))

        t.add_column(sa.Column("tenant_id", sa.String, unique=False, nullable=False, server_default="SYSTEM"))
        t.add_column(sa.Column("created_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("created_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("changed_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("changed_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("is_active", sa.Boolean, unique=False, nullable=False, server_default="TRUE"))


def downgrade():
    with op.batch_alter_table("reports", "public") as t:
        t.drop_column("description")
        t.drop_column("tags")

        t.drop_column("tenant_id")
        t.drop_column("created_by")
        t.drop_column("created_on")
        t.drop_column("changed_by")
        t.drop_column("changed_on")
        t.drop_column("is_active")
