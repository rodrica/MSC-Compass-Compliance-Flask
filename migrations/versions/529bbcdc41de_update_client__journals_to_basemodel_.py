"""Update client_*.journals to BaseModel structure and public schema

Revision ID: 529bbcdc41de
Revises: 0a0eaef1ca49
Create Date: 2022-03-30 15:29:46.646587

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '529bbcdc41de'
down_revision = '0a0eaef1ca49'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("journals", 
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
                              sa.ForeignKey("public.compliance_periods.id"))
                    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."journals"(internal_id, name,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    tenant_id, is_active, created_on, changed_on)
                SELECT id, text,
                    audit_id, audit_instruction_id, compliance_id, compliance_period_id,
                    '{}', TRUE,
                    NULL, NULL FROM "{}"."journals"
                '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("journals", "public")
