"""Update client_*.compliance_responces to BaseModel structure and public schema

Revision ID: a074038b3444
Revises: 45ad0708415a
Create Date: 2022-03-24 15:52:55.027957

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compass.models.int_enum import IntEnum

from techlock.compass.models.compliance_response import Phase, Status


# revision identifiers, used by Alembic.
revision = 'a074038b3444'
down_revision = '45ad0708415a'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("compliance_responses",
                    sa.Column('id', sa.Integer, primary_key=True),
                    # id from table in client schema for migration
                    sa.Column('internal_id', sa.Integer),

                    sa.Column("name",
                              sa.String,
                              unique=False,
                              nullable=False,
                              server_default=""),
                    sa.Column("description",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("tags", postgresql.JSONB, nullable=True),

                    sa.Column("tenant_id", sa.String, unique=False,
                              nullable=False),
                    sa.Column("created_by",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("changed_by",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("created_on",
                              sa.DateTime,
                              unique=False,
                              nullable=True),
                    sa.Column("changed_on",
                              sa.DateTime,
                              unique=False,
                              nullable=True),
                    sa.Column("is_active",
                              sa.Boolean,
                              unique=False,
                              nullable=False,
                              server_default="TRUE"),

                    sa.Column("compliance_id", sa.Integer,
                              sa.ForeignKey('public.compliances.id'),
                              nullable=False),
                    sa.Column("period_id", sa.Integer,
                              sa.ForeignKey('public.compliance_periods.id'),
                              nullable=False),
                    sa.Column("phase", IntEnum(Phase), nullable=False),
                    sa.Column("status", IntEnum(Status), nullable=False),
                    schema="public")
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."compliance_responses" (
                    internal_id, name,
                    compliance_id, period_id, phase, status,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT id, '',
                    compliance_id, period_id, phase, status,
                  '{}', TRUE, inserted_at, updated_at
                  FROM "{}"."compliance_responses"
            '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("compliance_responces", "public")
