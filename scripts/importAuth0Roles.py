#!/usr/bin/env python
'''
    Simple script to import Auth0 roles to flask db
'''
import argparse
import coloredlogs
import psycopg2
import logging

from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0

logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.INFO, fmt='%(message)s')


def main():
    args = parse_args()

    logger.info('Connecting services...')

    auth0 = get_auth0(args.domain, args.client_id, args.client_secret, args.audience)
    conn = psycopg2.connect(database=args.db_name, user=args.db_user, password=args.db_pass, host=args.db_host, port=args.db_port)

    logger.info('Listing roles...')
    roles = auth0.roles.list()['roles']
    for role in roles:
        role_name = role['name']
        role_desc = role['description']
        logger.info(f'  role {role_name} {role_desc}')

        with conn.cursor() as cursor:
            conn.autocommit = True
            cursor.execute(f'INSERT INTO roles (name, description, tenant_id, is_active) VALUES {"{role_name}", "{role_desc}", "{args.tenant_id}", True}')

    conn.close()


def get_auth0(domain, client_id, client_secret, audience):
    logger.info('Connecting to Auth0...')

    get_token = GetToken(domain)
    token = get_token.client_credentials(client_id, client_secret, audience)
    mgmt_api_token = token['access_token']

    auth0 = Auth0(domain, mgmt_api_token)
    logger.info('Connected')

    return auth0


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--audience', help='Auth0 Audience', type=str, required=True)
    parser.add_argument('-c', '--connection', help='Auth0 Connection to create the users in', type=str, required=True)
    parser.add_argument('-d', '--domain', help='Auth0 Domain', type=str, required=True)
    parser.add_argument('--client-id', help='Auth0 Client Id', type=str, required=True)
    parser.add_argument('--client-secret', help='Auth0 Client Secret', type=str, required=True)
    parser.add_argument('--db-host', help='Db host', type=str, required=True)
    parser.add_argument('--db-port', help='Db port', type=int, required=True)
    parser.add_argument('--db-user', help='Db user', type=str, required=True)
    parser.add_argument('--db-pass', help='Db password', type=str, required=True)
    parser.add_argument('--db-name', help='Db name', type=str, required=True)
    parser.add_argument('--tenant-id', help='Tenant id', type=str, required=True)

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
