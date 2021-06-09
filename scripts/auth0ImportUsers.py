#!/usr/bin/env python
'''
    Simple script to create Auth0 users based on an input csv file.
'''

import argparse
import csv
import json
import logging

import coloredlogs
import dpath.util
from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0

# Map csv to auth0. Supports nested destination mapping, and multiple destinations.
csv_to_auth0_mapping = {
    'Member ID': 'nickname',
    'First Name': 'given_name',
    'Last Name': 'family_name',
    'Email': ('email', 'name'),

    'Department': 'app_metadata.department',
    'Location': 'app_metadata.location',
    'Type': 'app_metadata.type',
    'Role ID': 'app_metadata.role_id',
    'Work Role': 'app_metadata.work_role',
    'Time Approver': 'app_metadata.time_approver',
    'Exp Approver': 'app_metadata.exp_approver',
    'Reports To': 'app_metadata.reports_to',
}

logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.INFO, fmt='%(message)s')


def main():
    args = parse_args()

    auth0 = get_auth0(args.domain, args.client_id, args.client_secret, args.audience)

    mapping = csv_to_auth0_mapping
    if args.mapping:
        with open(args.mapping) as fin:
            mapping = json.load(fin)

    logger.info('Creating users...')
    num_users = 0
    with open(args.file) as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            create_user(auth0, args.connection, mapping, row)
            num_users += 1

    logger.info('Created %s users', num_users)


def create_user(auth0, connection, mapping, row):
    user_obj = {
        'email_verified': True,
        'app_metadata': {},
        'user_metadata': {},
        'connection': connection,
        'password': 'changeM3!',
    }

    for src_key, dest_key in mapping.items():
        if isinstance(dest_key, tuple):
            for k in dest_key:
                update_dict(user_obj, k, row.get(src_key))
        else:
            update_dict(user_obj, dest_key, row.get(src_key))

    logger.debug('Creating user: %s', user_obj)
    auth0.users.create(user_obj)


def update_dict(d, path, value):
    dpath.util.new(d, path, value, separator='.')


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

    parser.add_argument('-f', '--file', help='Csv file to read users from', type=str, required=True)
    parser.add_argument('-m', '--mapping', help='Mapping file in json format, use this to override the default')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
