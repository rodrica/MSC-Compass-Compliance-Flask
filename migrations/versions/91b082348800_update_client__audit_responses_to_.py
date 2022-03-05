"""Update client_*.audit_responses to BaseModel structure and public schema

Revision ID: 91b082348800
Revises: a265765e02c9
Create Date: 2022-03-05 11:41:11.925842

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '91b082348800'
down_revision = 'a265765e02c9'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("audit_responses", 
                    sa.Column('id', sa.Integer, primary_key=True),
                    # id from table in client schema for migration
                    sa.Column('audit_id', sa.Integer, sa.ForeignKey("public.audits.id")),
                    sa.Column('instruction_id', sa.Integer,
                              sa.ForeignKey("public.report_instructions.id")),
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
                    sa.Column('compliance', sa.Integer),
                    )

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."audit_responses"(internal_id, name,
                audit_id, instruction_id, description, compliance,
                tenant_id, is_active, created_on, changed_on)
            SELECT id, '',
                audit_id, instruction_id, text, compliance,
                '{}', TRUE,
                inserted_at, updated_at FROM "{}"."audit_responses"
            '''.format(schema, schema)
            )

    op.execute("""
        CREATE OR REPLACE FUNCTION public.trigger_audit_response_insert_validate()
         RETURNS trigger
         LANGUAGE plpgsql
        AS $function$
        BEGIN
          IF ((SELECT notice FROM "public"."report_instructions" WHERE id = NEW.instruction_id) IS TRUE) THEN
            RAISE EXCEPTION 'Instruction % is a notice', NEW.instruction_id;
          END IF;
          RETURN NEW;
        END $function$
    """)

    op.execute("""
        CREATE TRIGGER trigger_audit_response_insert_validate
        AFTER INSERT ON "public"."audit_responses"
        FOR EACH ROW
        EXECUTE PROCEDURE
        "public".trigger_audit_response_insert_validate();
    """)

def downgrade():
    op.drop_table("audit_responses", "public")
