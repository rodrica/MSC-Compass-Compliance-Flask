"""Update client_*.compliance_period_periods to BaseModel structure and public schema

Revision ID: 96049162edef
Revises: 27011a074198
Create Date: 2022-03-16 10:38:14.660612

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '96049162edef'
down_revision = '27011a074198'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table(
        "compliance_periods",
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

        sa.Column(
            "compliance_id", sa.Integer,
            sa.ForeignKey('public.compliances.id'),
            nullable=False,
        ),
        sa.Column(
            "task_id", sa.Integer,
            sa.ForeignKey('public.compliance_tasks.id'),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        schema="public",
    )
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."compliance_periods"(internal_id, name,
                    start_date, end_date, compliance_id, task_id,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT id, name,
                  start_date, end_date, compliance_id, task_id,
                  '{}', TRUE, NULL, NULL FROM "{}"."compliance_periods"
            '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("compliance_periods", "public")
