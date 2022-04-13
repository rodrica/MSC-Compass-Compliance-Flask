"""Update client_*.compliance_responces_history to BaseModel structure and public schema

Revision ID: c9c7b14b2b60
Revises: a074038b3444
Create Date: 2022-03-24 21:09:04.593393

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compass.models.int_enum import IntEnum

from techlock.compass.models.compliance_response import Phase, Status


# revision identifiers, used by Alembic.
revision = 'c9c7b14b2b60'
down_revision = 'a074038b3444'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("compliance_responses_history",
                    sa.Column('history_id', sa.Integer, primary_key=True),
                    sa.Column('id', sa.Integer),
                    # id from table in client schema for migration
                    sa.Column('internal_id', sa.Integer),

                    sa.Column("name",
                              sa.String,
                              unique=False,
                              nullable=False,
                              server_default=""),
                    sa.Column("description",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("tags", postgresql.JSONB, nullable=True),

                    sa.Column("tenant_id", sa.String, unique=False,
                              nullable=False),
                    sa.Column("created_by",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("changed_by",
                              sa.String,
                              unique=False,
                              nullable=True),
                    sa.Column("created_on",
                              sa.DateTime,
                              unique=False,
                              nullable=True),
                    sa.Column("changed_on",
                              sa.DateTime,
                              unique=False,
                              nullable=True),
                    sa.Column("is_active",
                              sa.Boolean,
                              unique=False,
                              nullable=False,
                              server_default="TRUE"),

                    sa.Column("compliance_id", sa.Integer,
                              sa.ForeignKey('public.compliances.id'),
                              nullable=False),
                    sa.Column("period_id", sa.Integer,
                              sa.ForeignKey('public.compliance_periods.id'),
                              nullable=False),
                    sa.Column("phase", IntEnum(Phase), nullable=False),
                    sa.Column("status", IntEnum(Status), nullable=False),
                    schema="public")
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO "public"."compliance_responses_history" (
                    internal_id, id, name,
                    compliance_id, period_id, phase, status,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT history_id, id, '',
                    compliance_id, period_id, phase, status,
                  '{}', TRUE, inserted_at, updated_at
                  FROM "{}"."compliance_responses_history"
            '''.format(schema, schema)
            )

    op.execute("""
    CREATE OR REPLACE FUNCTION public.trigger_history_compliance_responses()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    BEGIN
      INSERT INTO "public"."compliance_responses_history"
      SELECT nextval('public.compliance_responses_history_history_id_seq'::regclass), OLD.*;
      RETURN NEW;
    END $function$
    """
               )

    op.execute("""
        CREATE TRIGGER trigger_history_compliance_responses
        AFTER UPDATE ON "public"."compliance_responses"
        FOR EACH ROW
        EXECUTE PROCEDURE "public".trigger_history_compliance_responses();
    """)



def downgrade():
    op.drop_table("compliance_responces_history", "public")
