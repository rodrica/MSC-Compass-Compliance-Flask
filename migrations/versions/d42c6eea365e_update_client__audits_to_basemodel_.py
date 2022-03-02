"""Update client_*.audits to BaseModel structure

Revision ID: d42c6eea365e
Revises: 275d6e3ea274
Create Date: 2022-02-25 13:16:06.825951

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from techlock.compas.models.audit import Phase

from techlock.compas.models.int_enum import IntEnum



# revision identifiers, used by Alembic.
revision = 'd42c6eea365e'
down_revision = '275d6e3ea274'
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    ins = sa.inspect(engine)
    schemas = ins.get_schema_names()

    op.create_table("audits", 
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
                '''INSERT INTO "public"."audits"(internal_id, name, reports,
                estimated_end_date,
                start_date, estimated_remediation_date,
                remediation_date, end_date, phase, user_id, tenant_id,
                is_active, created_on, changed_on)
            SELECT id, name, reports, estimated_end_date,
                start_date, estimated_remediation_date,
                remediation_date, end_date, phase, user_id, '{}', not deleted,
                inserted_at, updated_at FROM "{}"."audits"
            '''.format(schema, schema)
            )

            # TODO: Create a schemas clear migration
            # op.drop_table("audits", schema=schema)


def downgrade():
    op.drop_table("audits", "public")
    # TODO: probably clear schemas rollback, not here
    # engine = op.get_bind()
    # ins = sa.inspect(engine)
    # schemas = ins.get_schema_names()
    # for schema in schemas:
    #     if schema not in ('public', 'information_schema'):
    #         op.create_table("audits", 
    #                         sa.Column('id', sa.Integer, primary_key=True),
    #                         sa.Column("name", sa.String, unique=False, nullable=False, server_default=""),

    #                         sa.Column("inserted_at", sa.DateTime, unique=False, nullable=True),
    #                         sa.Column("updated_at", sa.DateTime, unique=False, nullable=True),
    #                         sa.Column("deleted", sa.Boolean, unique=False, nullable=False, server_default="TRUE"),
    #                         sa.Column("user_id", sa.String, nullable=False),
    #                         sa.Column("reports", postgresql.ARRAY(sa.Integer),
    #                                   nullable=False),
    #                         sa.Column("start_date", sa.Date, nullable=False),
    #                         sa.Column("estimated_remediation_date", sa.Date),
    #                         sa.Column("remediation_date", sa.Date),
    #                         sa.Column("estimated_end_date", sa.Date,
    #                                   nullable=False),
    #                         sa.Column("end_date", sa.Date),
    #                         sa.Column("phase", IntEnum(Phase),
    #                                   default=Phase.scoping_and_validation),
    #                         schema=schema)
    #         #op.execute(
    #         #    '''INSERT INTO "{}"."audits"(id, name, reports,
    #         #    estimated_end_date,
    #         #    start_date, estimated_remediation_date,
    #         #    remediation_date, end_date, phase, user_id,
    #         #     deleted, inserted_at, updated_at)
    #         #SELECT internal_id, name, reports, estimated_end_date,
    #         #    start_date, estimated_remediation_date,
    #         #    remediation_date, end_date, phase, user_id,
    #         #    not is_active, created_on, changed_on
    #         #    FROM "public"."audits"
    #         #    WHERE tenant_id={}
    #         #'''.format(schema, schema)
    #         #)
    #         pass
