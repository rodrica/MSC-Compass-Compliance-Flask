#!/usr/bin/env python
'''
    Simple script to import Auth0 roles to flask db
'''
import argparse
import logging

import coloredlogs
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0

logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.INFO, fmt='%(message)s')


def main():
    args = parse_args()

    logger.info('Connecting services...')

    auth0 = get_auth0(args.domain, args.client_id, args.client_secret, args.audience)

#    auth0_user = auth0.users.get('auth0|5e1776bb5fe9de0dc65a5650')
#    auth0.users.add_roles(auth0_user['user_id'], ['rol_8nYXDvS8JJ2pO18Y'])

    logger.info('Listing roles...')
    roles = auth0.roles.list()['roles']
    for role in roles:
        role_id = role['id']
        role_name = role['name']
        role_desc = role['description']
        logger.info(f'  role {role_id},{role_name},{role_desc}')
        users = auth0.roles.list_users(role['id'])['users']
        for user in users:
            user_id = user['user_id']
            name = user['name']
            email = user['email']
            logger.info(f'     user {user_id},{name},{email}')

#        if role_name=="tenant1_Alpha":
#            auth0.roles.add_users(role['id'], ['auth0|5db3abd5d273330e147f534c', 'auth0|5dd35fe92b99b00d2feb2331'])
#            auth0.roles.add_users(role['id'], ['auth0|5e1776bb5fe9de0dc65a5650'])


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

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
