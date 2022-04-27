"""Update report_nodes to BaseModel structure

Revision ID: a9bba50d9954
Revises: 3f669c7d24f3
Create Date: 2022-02-21 16:30:58.796154

"""
from enum import unique

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool

# revision identifiers, used by Alembic.
revision = 'a9bba50d9954'
down_revision = '3f669c7d24f3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("report_nodes", "public") as t:
        t.add_column(sa.Column("name", sa.String, unique=False, nullable=False, server_default=""))
        t.add_column(sa.Column("description", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("tags", postgresql.JSONB, nullable=True))

        t.add_column(sa.Column("tenant_id", sa.String, unique=False, nullable=False, server_default="SYSTEM"))
        t.add_column(sa.Column("created_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("created_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("changed_by", sa.String, unique=False, nullable=True))
        t.add_column(sa.Column("changed_on", sa.DateTime, unique=False, nullable=True))
        t.add_column(sa.Column("is_active", sa.Boolean, unique=False, nullable=False, server_default="TRUE"))


def downgrade():
    with op.batch_alter_table("report_nodes", "public") as t:
        t.drop_column("name")
        t.drop_column("description")
        t.drop_column("tags")

        t.drop_column("tenant_id")
        t.drop_column("created_by")
        t.drop_column("created_on")
        t.drop_column("changed_by")
        t.drop_column("changed_on")
        t.drop_column("is_active")
