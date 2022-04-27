"""Update report_nodes to BaseModel structure

Revision ID: 3f669c7d24f3
Revises: f4a1fa3c2b9d
Create Date: 2022-02-18 13:47:57.554532

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f669c7d24f3'
down_revision = 'f4a1fa3c2b9d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("report_versions", "public") as t:
        t.alter_column("version", new_column_name="name")
        t.add_column(sa.Column("description", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("tags", postgresql.JSONB, nullable=True))

        t.add_column(sa.Column("tenant_id", sa.String, unique=False, nullable=False, server_default="SYSTEM"))
        t.add_column(sa.Column("created_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("created_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("changed_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("changed_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("is_active", sa.Boolean, unique=False, nullable=False, server_default="TRUE"))


def downgrade():
    with op.batch_alter_table("report_versions", "public") as t:
        t.alter_column("name", new_column_name="version")
        t.drop_column("description")
        t.drop_column("tags")

        t.drop_column("tenant_id")
        t.drop_column("created_by")
        t.drop_column("created_on")
        t.drop_column("changed_by")
        t.drop_column("changed_on")
        t.drop_column("is_active")
