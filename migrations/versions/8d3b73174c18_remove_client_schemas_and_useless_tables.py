"""Remove client schemas and useless tables

Revision ID: 8d3b73174c18
Revises: 9c011b685c07
Create Date: 2022-04-15 15:15:56.954154

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8d3b73174c18'
down_revision = '9c011b685c07'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    for schema in schemas:
        if schema not in ('public', 'information_schema'):
            with op.get_context().autocommit_block():
                op.execute("DROP SCHEMA {} CASCADE;".format(schema))

    for table in ('user_global_permissions', 'schema_migrations', 'users'):
        op.drop_table(table)

def downgrade():
    pass
