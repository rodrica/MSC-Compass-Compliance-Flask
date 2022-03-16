"""Update client_*.compliances_history to BaseModel structure and public schema

Revision ID: 27011a074198
Revises: ac52a835f99f
Create Date: 2022-03-16 10:00:38.560991

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compas.models.int_enum import IntEnum

from techlock.compas.models.compliance import Plan


# revision identifiers, used by Alembic.
revision = '27011a074198'
down_revision = 'ac52a835f99f'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("compliances_history", 
                    sa.Column('history_id', sa.Integer, primary_key=True),
                    sa.Column('id', sa.Integer),
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

                    sa.Column("user_id", sa.String),
                    sa.Column("tasks", postgresql.ARRAY(sa.Integer)),
                    sa.Column("start_date", sa.Date),
                    sa.Column("end_date", sa.Date),
                    sa.Column("plan", IntEnum(Plan)),
                    schema="public")
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute(
                '''INSERT INTO
                "public"."compliances_history"(internal_id, id, name,
                    tasks, start_date, end_date, plan, user_id,
                    tenant_id, is_active, created_on, changed_on)
                  SELECT history_id, id, name,
                  tasks, start_date, end_date, plan, user_id, 
                  '{}', not deleted, inserted_at, updated_at FROM "{}"."compliances_history"
            '''.format(schema, schema)
            )

    op.execute("""
    CREATE OR REPLACE FUNCTION public.trigger_history_compliances()
     RETURNS trigger
     LANGUAGE plpgsql
    AS $function$
    BEGIN
      INSERT INTO "public"."compliances_history"
      SELECT nextval('public.compliances_history_history_id_seq'::regclass), OLD.*;
      RETURN NEW;
    END $function$
    """
               )

    op.execute("""
        CREATE TRIGGER trigger_history_compliances
        AFTER UPDATE ON "public"."compliances"
        FOR EACH ROW
        EXECUTE PROCEDURE "public".trigger_history_compliances();
    """)


def downgrade():
    op.drop_table("compliances_history", "public")
