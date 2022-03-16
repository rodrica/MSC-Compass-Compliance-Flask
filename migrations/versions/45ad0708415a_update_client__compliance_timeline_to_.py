"""Update client_*.compliances_timeline to BaseModel structure and public schema

Revision ID: 45ad0708415a
Revises: 96049162edef
Create Date: 2022-03-16 16:31:01.035268

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '45ad0708415a'
down_revision = '96049162edef'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("compliances_timeline", 
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

                    sa.Column("compliance_id", sa.Integer,
                              sa.ForeignKey('public.compliances.id'),
                              nullable=False),
                    sa.Column("date", sa.Date, nullable=False),
                    sa.Column("pending", sa.Integer, nullable=False),
                    sa.Column("passed", sa.Integer, nullable=False),
                    sa.Column("failed", sa.Integer, nullable=False),
                    sa.Column("remediation", sa.Integer, nullable=False),
                    sa.Column("overdue", sa.Integer, nullable=False),
                    schema="public")
    op.create_index('compliances_timeline_tenant_id_compliance_id_date_index',
                    'compliances_timeline', ['tenant_id', 'compliance_id', 'date'],
                    schema="public", unique=True)
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."compliances_timeline"(internal_id, name,
                    compliance_id, date, pending, passed, failed,
                    remediation, overdue,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT id, '',
                    compliance_id, date, pending, passed, failed,
                    remediation, overdue,
                  '{}', TRUE, NULL, NULL FROM "{}"."compliances_timeline"
            '''.format(schema, schema)
            )
    pass


def downgrade():
    op.drop_table("compliances_timeline", "public")
