"""Migrate users from Auth0 ids to emails

Revision ID: 9c011b685c07
Revises: 614e51ebb92c
Create Date: 2022-04-15 14:07:12.965492

"""
from alembic import op
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from techlock.common import AuthInfo, ConfigManager

# revision identifiers, used by Alembic.
revision = '9c011b685c07'
down_revision = '614e51ebb92c'
branch_labels = None
depends_on = None


cm = ConfigManager()
current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
domain = cm.get(current_user, 'auth0.domain', raise_if_not_found=True)
client_id = cm.get(current_user, 'auth0.client_id', raise_if_not_found=True)
client_secret = cm.get(current_user, 'auth0.client_secret', raise_if_not_found=True)
audience = cm.get(current_user, 'auth0.audience', raise_if_not_found=True)
get_token = GetToken(domain)
token = get_token.client_credentials(client_id, client_secret, audience)
mgmt_api_token = token['access_token']

auth0 = Auth0(domain, mgmt_api_token)

users_num = auth0.users.list(fields=[], per_page=0)['total']
users = auth0.users.list(fields=['user_id', 'email'], per_page=users_num, include_totals=False)
user_values = ", ".join(["('{}', '{}')".format(u['user_id'], u['email']) for u in users])

TABLES = [
    'audits',
    'audits_history',
    'comments',
    'compliances',
    'compliances_history',
    'events',
    'uploads',
]

def upgrade():
    for table in TABLES:
        q = """UPDATE "public".{}  AS t
                SET user_id=c.email
                FROM(values {}) AS c(auth0_id, email)
                WHERE c.auth0_id = t.user_id""".format(table, user_values)

        op.execute(q)


def downgrade():
    for table in TABLES:
        q = """UPDATE "public".{}  AS t
                SET user_id=c.auth0_id
                FROM(values {}) AS c(auth0_id, email)
                WHERE c.email = t.user_id""".format(table, user_values)

        op.execute(q)
