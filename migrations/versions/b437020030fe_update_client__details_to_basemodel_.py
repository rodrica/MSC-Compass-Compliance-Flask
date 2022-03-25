"""Update client_*.details to BaseModel structure and public schema

Revision ID: b437020030fe
Revises: 07b8995145c0
Create Date: 2022-03-25 10:19:55.501647

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import True_


# revision identifiers, used by Alembic.
revision = 'b437020030fe'
down_revision = '07b8995145c0'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("details", 
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

                    sa.Column("code", sa.String, nullable=False),

                    sa.Column("compliant_until", sa.Date,
                              nullable=True),
                    sa.Column("timestamp", sa.TIMESTAMP,
                              nullable=False),
                    sa.Column("timezone", sa.String, nullable=False)
                    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."details"(internal_id, name,
                    code, compliant_until, timestamp, timezone,
                    tenant_id, is_active, created_on, changed_on)
                SELECT id, name,
                    code, compliant_until, timestamp, timezone,
                    '{}', not deleted,
                    NULL, NULL FROM "{}"."details"
                '''.format(schema, schema)
            )


def downgrade():
    op.drop_table("details", "public")
