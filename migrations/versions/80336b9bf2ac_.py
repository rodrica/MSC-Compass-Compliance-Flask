"""empty message

Revision ID: 80336b9bf2ac
Revises: 48800f419866
Create Date: 2019-11-16 00:20:13.015496

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80336b9bf2ac'
down_revision = '48800f419866'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tenants', sa.Column('service_now_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tenants', 'service_now_id')
    # ### end Alembic commands ###