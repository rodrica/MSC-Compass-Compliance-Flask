"""Update client_*.comments to BaseModel structure and public schema

Revision ID: 07b8995145c0
Revises: c9c7b14b2b60
Create Date: 2022-03-25 09:09:40.429873

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '07b8995145c0'
down_revision = 'c9c7b14b2b60'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table(
        "comments",
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
            'audit_id',
            sa.Integer,
            sa.ForeignKey("public.audits.id"),
        ),
        sa.Column(
            'audit_instruction_id',
            sa.Integer,
            sa.ForeignKey("public.report_instructions.id"),
        ),
        sa.Column(
            'compliance_id',
            sa.Integer,
            sa.ForeignKey("public.compliances.id"),
        ),
        sa.Column(
            'compliance_period_id',
            sa.Integer,
            sa.ForeignKey("public.compliance_periods.id"),
        ),

        sa.Column("timestamp", sa.TIMESTAMP, nullable=False),
    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."comments"(internal_id, name, description,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    user_id, timestamp,
                    tenant_id, is_active, created_on, changed_on)
                SELECT id, '', text,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    user_id, timestamp,
                    '{}', TRUE,
                    NULL, NULL FROM "{}"."comments"
                '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("comments", "public")
