"""Update client_*.events to BaseModel structure and public schema

Revision ID: 0a0eaef1ca49
Revises: b437020030fe
Create Date: 2022-03-25 16:52:03.952377

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import True_
from techlock.compas.models.int_enum import IntEnum

from techlock.compas.models.event import Type, Visibility


# revision identifiers, used by Alembic.
revision = '0a0eaef1ca49'
down_revision = 'b437020030fe'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("events", 
                    sa.Column('id', sa.Integer, primary_key=True),
                    # id from table in client schema for migration
                    sa.Column('internal_id', sa.Integer),

                    sa.Column("name", sa.String, unique=False, nullable=False, server_default=""),
                    sa.Column("description", sa.String, unique=False, nullable=True),
                    sa.Column("tags", postgresql.JSONB, nullable=True),

                    sa.Column("tenant_id", sa.String, unique=False,
                              nullable=False),
                    sa.Column("created_by", sa.String, unique=False, nullable=True),
                    sa.Column("changed_by", sa.String, unique=False, nullable=True),
                    sa.Column("created_on", sa.DateTime, unique=False, nullable=True),
                    sa.Column("changed_on", sa.DateTime, unique=False, nullable=True),
                    sa.Column("is_active", sa.Boolean, unique=False, nullable=False, server_default="TRUE"),

                    sa.Column("user_id", sa.String, nullable=True),

                    sa.Column('audit_id',
                              sa.Integer,
                              sa.ForeignKey("public.audits.id")),
                    sa.Column('audit_instruction_id',
                              sa.Integer,
                              sa.ForeignKey("public.report_instructions.id")),
                    sa.Column('compliance_id',
                              sa.Integer,
                              sa.ForeignKey("public.compliances.id")),
                    sa.Column('compliance_period_id',
                              sa.Integer,
                              sa.ForeignKey("public.compliance_periods.id")),

                    sa.Column("timestamp", sa.TIMESTAMP,
                              nullable=False),
                    sa.Column("type", IntEnum(Type),
                              nullable=False),
                    sa.Column("visibility", IntEnum(Visibility),
                              nullable=False)
                    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."events"(internal_id, name, description,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    user_id, timestamp, type, visibility,
                    tenant_id, is_active, created_on, changed_on)
                SELECT id, '', text,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    user_id, timestamp, type, visibility,
                    '{}', TRUE,
                    NULL, NULL FROM "{}"."events"
                '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("events", "public")
