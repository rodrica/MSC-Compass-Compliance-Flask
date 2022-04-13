"""Update client_*.audits_timeline to BaseModel structure and public schema

Revision ID: a265765e02c9
Revises: caf08fc6272a
Create Date: 2022-03-02 20:29:10.354272

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compass.models.audit import Phase

from techlock.compass.models.int_enum import IntEnum


# revision identifiers, used by Alembic.
revision = 'a265765e02c9'
down_revision = 'caf08fc6272a'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("audits_timeline", 
                    sa.Column('id', sa.Integer, primary_key=True),
                    # id from table in client schema for migration
                    sa.Column('audit_id', sa.Integer, sa.ForeignKey("public.audits.id")),
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
                    sa.Column("date", sa.Date, nullable=False),
                    sa.Column("compliant", sa.Integer, nullable=False),
                    sa.Column("notice", sa.Integer, nullable=False),
                    sa.Column("noncompliant", sa.Integer,
                              nullable=False),
                    sa.Column("pending", sa.Integer, nullable=False),
                    )
    op.create_index('audits_timeline_tenant_id_audit_id_date_index',
                    'audits_timeline', ['tenant_id', 'audit_id', 'date'],
                    schema="public", unique=True)

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."audits_timeline"(internal_id, name,
                audit_id, date, compliant, notice, noncompliant, pending,
                tenant_id, is_active, created_on, changed_on)
            SELECT id, '',
                audit_id, date, compliant, notice, noncompliant, pending,
                '{}', TRUE,
                NULL, NULL FROM "{}"."audits_timeline"
            '''.format(schema, schema)
            )



def downgrade():
    op.drop_table("audits_timeline", "public")
