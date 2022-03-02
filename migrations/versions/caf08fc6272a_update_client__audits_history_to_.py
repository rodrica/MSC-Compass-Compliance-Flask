"""Update client_*.audits_history to BaseModel structure and public schema

Revision ID: caf08fc6272a
Revises: d42c6eea365e
Create Date: 2022-03-01 10:56:59.262680

"""
from alembic import op
from alembic.context import execute
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import True_

from techlock.compas.models.audit import Phase

from techlock.compas.models.int_enum import IntEnum


# revision identifiers, used by Alembic.
revision = 'caf08fc6272a'
down_revision = 'd42c6eea365e'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("audits_history", 
                    sa.Column('history_id', sa.Integer, primary_key=True),
                    # id from table in client schema for migration
                    sa.Column('id', sa.Integer),
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
                    sa.Column("reports", postgresql.ARRAY(sa.Integer),
                              nullable=True),
                    sa.Column("start_date", sa.Date, nullable=True),
                    sa.Column("estimated_remediation_date", sa.Date),
                    sa.Column("remediation_date", sa.Date),
                    sa.Column("estimated_end_date", sa.Date,
                              nullable=True),
                    sa.Column("end_date", sa.Date),
                    sa.Column("phase", IntEnum(Phase),
                              default=Phase.scoping_and_validation),
                    schema="public")
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."audits_history"(internal_id, id,
                name, reports,
                estimated_end_date,
                start_date, estimated_remediation_date,
                remediation_date, end_date, phase, user_id, tenant_id,
                is_active, created_on, changed_on)
            SELECT history_id, id, name, reports, estimated_end_date,
                start_date, estimated_remediation_date,
                remediation_date, end_date, phase, user_id, '{}', not deleted,
                inserted_at, updated_at FROM "{}"."audits_history"
            '''.format(schema, schema)
            )

    op.execute("""
    CREATE OR REPLACE FUNCTION public.trigger_history_audits()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    BEGIN
      INSERT INTO "public"."audits_history"
      SELECT nextval('public.audits_history_history_id_seq'::regclass), OLD.*;
      RETURN NEW;
    END $function$
    """
               )

    op.execute("""
        CREATE TRIGGER trigger_history_audits
        AFTER UPDATE ON "public"."audits"
        FOR EACH ROW
        EXECUTE PROCEDURE "public".trigger_history_audits();
    """)


            # TODO: Create a schemas clear migration
            # op.drop_table("audits", schema=schema)


def downgrade():
    op.drop_table("audits_history", "public")
    op.execute("""DROP TRIGGER trigger_history_audits ON "public"."audits" """)
    op.execute("""DROP FUNCTION trigger_history_audits""")
