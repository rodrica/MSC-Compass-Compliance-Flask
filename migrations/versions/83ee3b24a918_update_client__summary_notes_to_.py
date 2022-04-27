"""Update client_*.summary_notes to BaseModel structure and public schema

Revision ID: 83ee3b24a918
Revises: 529bbcdc41de
Create Date: 2022-03-30 15:47:33.855179

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '83ee3b24a918'
down_revision = '529bbcdc41de'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table(
        "summary_notes",
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
            'audit_id',
            sa.Integer,
            sa.ForeignKey("public.audits.id"),
        ),
        sa.Column(
            'compliance_id',
            sa.Integer,
            sa.ForeignKey("public.compliances.id"),
        ),
    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."summary_notes"(
                internal_id, name,
                    audit_id, compliance_id,
                    tenant_id, is_active, created_on, changed_on)
                SELECT id, text,
                    audit_id, compliance_id,
                    '{}', TRUE,
                    NULL, NULL FROM "{}"."summary_notes"
                '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("summary_notes", "public")
