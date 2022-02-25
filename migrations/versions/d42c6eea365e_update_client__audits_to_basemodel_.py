"""Update client_*.audits to BaseModel structure

Revision ID: d42c6eea365e
Revises: 275d6e3ea274
Create Date: 2022-02-25 13:16:06.825951

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision = 'd42c6eea365e'
down_revision = '275d6e3ea274'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            op.execute('UPDATE "{}"."{}" SET deleted=not deleted'.format(schema, "audits"))
            with op.batch_alter_table("audits", schema) as t:
                t.add_column(sa.Column("description", sa.String, unique=False, nullable=True))
                t.add_column(sa.Column("tags", postgresql.JSONB, nullable=True))

                t.add_column(sa.Column("tenant_id", sa.String, unique=False,
                                       nullable=False, server_default=schema))
                t.add_column(sa.Column("created_by", sa.String, unique=False, nullable=True))
                t.alter_column("inserted_at", new_column_name="created_on")
                t.alter_column("updated_at", new_column_name="changed_on")
                t.add_column(sa.Column("changed_by", sa.String, unique=False, nullable=True))
                t.alter_column("deleted", new_column_name="is_active")


def downgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()
    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            with op.batch_alter_table("audits", schema) as t:
                t.drop_column("description")
                t.drop_column("tags")

                t.drop_column("tenant_id")
                t.drop_column("created_by")
                t.alter_column("created_on", new_column_name="inserted_at")
                t.alter_column("changed_on", new_column_name="updated_at")
                t.drop_column("changed_by")
                t.alter_column("is_active", new_column_name="deleted")
            op.execute('UPDATE "{}"."{}" SET deleted=not deleted'.format(schema, "audits"))
