"""Update client_*.compliances to BaseModel structure and public schema

Revision ID: ac52a835f99f
Revises: 247ebb04c1a4
Create Date: 2022-03-14 15:55:21.697827

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from techlock.compass.models.compliance import Plan
from techlock.compass.models.int_enum import IntEnum

# revision identifiers, used by Alembic.
revision = 'ac52a835f99f'
down_revision = '247ebb04c1a4'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table(
        "compliances",
        sa.Column('id', sa.Integer, primary_key=True),
        # id from table in client schema for migration
        sa.Column('internal_id', sa.Integer),

        sa.Column("name", sa.String, unique=False, nullable=False, server_default=""),
        sa.Column("description", sa.String, unique=False, nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),

        sa.Column(
            "tenant_id", sa.String, unique=False,
            nullable=False,
        ),
        sa.Column("created_by", sa.String, unique=False, nullable=True),
        sa.Column("changed_by", sa.String, unique=False, nullable=True),
        sa.Column("created_on", sa.DateTime, unique=False, nullable=True),
        sa.Column("changed_on", sa.DateTime, unique=False, nullable=True),
        sa.Column("is_active", sa.Boolean, unique=False, nullable=False, server_default="TRUE"),

        sa.Column("user_id", sa.String, nullable=False),
        sa.Column(
            "tasks", postgresql.ARRAY(sa.Integer),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date),
        sa.Column("plan", IntEnum(Plan), nullable=False),
        schema="public",
    )
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."compliances"(internal_id, name,
                    tasks, start_date, end_date, plan, user_id,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT id, name,
                  tasks, start_date, end_date, plan, user_id,
                  '{}', not deleted, inserted_at, updated_at FROM "{}"."compliances"
            '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("compliances", "public")
