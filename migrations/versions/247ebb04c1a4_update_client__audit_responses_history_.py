"""Update client_*.audit_responses_history to BaseModel structure and public schema

Revision ID: 247ebb04c1a4
Revises: 91b082348800
Create Date: 2022-03-10 19:04:14.693075

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compas.models.audit import Phase

from techlock.compas.models.int_enum import IntEnum


# revision identifiers, used by Alembic.
revision = '247ebb04c1a4'
down_revision = '91b082348800'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("audit_responses_history", 
                    sa.Column('history_id', sa.Integer, primary_key=True),
                    sa.Column('id', sa.Integer),
                    # id from table in client schema for migration
                    sa.Column('audit_id', sa.Integer,
                              sa.ForeignKey("public.audits.id"),
                              nullable=False),
                    sa.Column('instruction_id', sa.Integer,
                              sa.ForeignKey("public.report_instructions.id"),
                              nullable=False),
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
                    sa.Column('compliance', sa.Integer, nullable=False),
                    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."audit_responses_history"(
                internal_id, id, name,
                audit_id, instruction_id, description, compliance,
                tenant_id, is_active, created_on, changed_on)
            SELECT history_id,id, '',
                audit_id, instruction_id, text, compliance,
                '{}', TRUE,
                inserted_at, updated_at FROM
                "{}"."audit_responses_history"
            '''.format(schema, schema)
            )
    pass
    op.execute("""
    CREATE OR REPLACE FUNCTION public.trigger_history_audit_responses()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    BEGIN
      INSERT INTO "public"."audit_responses_history"
      SELECT nextval('public.audit_responses_history_history_id_seq'::regclass), OLD.*;
      RETURN NEW;
    END $function$
    """
               )

    op.execute("""
        CREATE TRIGGER trigger_history_audit_responses
        AFTER UPDATE ON "public"."audit_responses"
        FOR EACH ROW
        EXECUTE PROCEDURE "public".trigger_history_audit_responses();
    """)



def downgrade():
    op.drop_table("audit_responses_history", "public")
