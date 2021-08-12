from __future__ import annotations

import logging
import os
import random
import string
import time
from typing import TYPE_CHECKING, Dict, List

import jinja2
import jwt
from auth0.v3.authentication import GetToken
from auth0.v3.exceptions import Auth0Error
from auth0.v3.management import Auth0
from techlock.common import AuthInfo, AwsUtils, ConfigManager, read_file
from techlock.common.api import BadRequestException, ConflictException, NotFoundException

from .base import IdpProvider

if TYPE_CHECKING:
    from ...models import Role, User

logger = logging.getLogger(__name__)
STAGE = os.environ.get('STAGE', 'dev').upper()

TENANT_BASE_ROLE_NAME = '_BASE_'
DEFAULT_EMAIL_TXT_URL = 'py://techlock/user_management_service/services/identity_providers/email_templates/invite_email.txt'
DEFAULT_EMAIL_HTML_URL = 'py://techlock/user_management_service/services/identity_providers/email_templates/invite_email.html'

_app_metadata_keys = [
]


def _generate_password() -> str:
    charset = string.ascii_letters + string.digits + string.punctuation

    return ''.join(random.sample(charset, 24))


class Auth0Idp(IdpProvider):
    def __init__(self):
        current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
        self.connection_id = ConfigManager().get(current_user, 'auth0.connection_id', raise_if_not_found=True)

        self._refresh_token()

    def _refresh_token(self):
        cm = ConfigManager()
        current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
        domain = cm.get(current_user, 'auth0.domain', raise_if_not_found=True)
        client_id = cm.get(current_user, 'auth0.client_id', raise_if_not_found=True)
        client_secret = cm.get(current_user, 'auth0.client_secret', raise_if_not_found=True)
        audience = cm.get(current_user, 'auth0.audience', raise_if_not_found=True)

        get_token = GetToken(domain)
        token = get_token.client_credentials(client_id, client_secret, audience)
        mgmt_api_token = token['access_token']

        # Keep track of expiration
        # Note that we don't verify the token. We're only getting the expiration value.
        #   Not concerned about tampering.
        token_payload = jwt.decode(mgmt_api_token, verify=False)
        self.token_expiration = token_payload['exp']

        self.auth0 = Auth0(domain, mgmt_api_token)

    def _is_refresh_needed(self):
        # Expire 60 second earlier - This prevents the scenario where the request expires after we checked.
        now = int(time.time())
        # Is
        is_refresh_needed = self.token_expiration - 60 < now

        logger.debug(
            'Auth0: Checking if Auth0 token refresh is needed.', extra={
                'token_expiration': self.token_expiration,
                'time': now,
                'is_needed': is_refresh_needed,
            },
        )

        return is_refresh_needed

    def _refresh_if_needed(self):
        try:
            if self._is_refresh_needed():
                self._refresh_token()
        except Exception as e:
            logger.error(f'Auth0: Failed to refresh token. Error={e}')

    def _handle_token_error(self, callback):
        '''
            Handle token expired error and refresh.
            While calling `self._refresh_if_needed()` before should fix it. This just handles the odd case that it didn't.
        '''
        try:
            return callback()
        except Auth0Error as e:
            if 'expired token' in e.message.lower():
                logger.error('Auth0: Token expired, refreshing and trying again.')
                self._refresh_token()
                return callback()
            else:
                raise

    def _password_strength_error(self, e):
        conn_options = self.auth0.connections.get(self.connection_id)['options']

        raise BadRequestException(
            'Password is too weak.', payload={
                'rules': {
                    'min_length': conn_options['password_complexity_options']['min_length'],
                    'history_size': conn_options['password_history']['size'],
                    'no_personal_info': conn_options['password_no_personal_info']['enabled'],
                    'must_incl_number': conn_options['passwordPolicy'] in ('fair', 'good', 'excellent'),
                    'must_incl_special': conn_options['passwordPolicy'] in ('good', 'excellent'),
                    'no_consecutive': conn_options['passwordPolicy'] == 'excellent',
                },
            },
        )

    def _get_user(self, user: User):
        self._refresh_if_needed()
        found_users = self._handle_token_error(
            lambda: self.auth0.users.list(
                q=f'identities.connection: "{self.connection_id}" AND email: "{user.email}"',
            ),
        )
        total_found_users = found_users['total']
        if not total_found_users:
            logger.error('Auth0: User not found', extra={'user': user.entity_id})
            raise NotFoundException('User not found')
        elif total_found_users > 1:
            logger.warn(
                'Auth0: Found multiple users, expected one. Will use first one.', extra={
                    'found_users': found_users,
                },
            )

        return found_users['users'][0]

    def _get_role(self, role_name: str, throw_if_not_found: bool = True):
        self._refresh_if_needed()
        roles = self.auth0.roles.list(name_filter=role_name)['roles']
        if len(roles) > 1:
            logger.warn(
                'Found multiple roles, expected one. Will use first one.', extra={
                    'roles': roles,
                },
            )

        for role in roles:
            if role['name'] == role_name:
                return role

        if throw_if_not_found:
            logger.error(f'Role {role_name} not found')
            raise NotFoundException('Role not found')
        else:
            return None

    def _generate_password_change_link(
        self,
        current_user: AuthInfo,
        user: User,
    ):
        cm = ConfigManager()
        client_id = cm.get(current_user, 'invite.client_id', raise_if_not_found=True)
        connection_id = cm.get(current_user, 'invite.connection_id', raise_if_not_found=True)
        ttl = cm.get(current_user, 'invite.ttl', 86400 * 3)  # 3 days
        resp = self._handle_token_error(
            lambda: self.auth0.tickets.create_pswd_change({
                'client_id': client_id,
                'connection_id': connection_id,
                'email': user.email,
                'ttl_sec': ttl,
                'mark_email_as_verified': True,
            }),
        )

        return resp['ticket']

    def _send_invite_email(
        self,
        current_user: AuthInfo,
        user: User,
    ):
        cm = ConfigManager()
        src_email = cm.get(current_user, 'invite.src_email', 'Tech Lock Administrator <tl-admin@msc.techlockinc.com>')
        subject = cm.get(current_user, 'invite.subject', 'Welcome to the Tech Lock NDR Portal!')
        text_tmpl = read_file(cm.get(current_user, 'invite.text_url', DEFAULT_EMAIL_TXT_URL)).decode('utf8')
        html_tmpl = read_file(cm.get(current_user, 'invite.html_url', DEFAULT_EMAIL_HTML_URL)).decode('utf8')

        url = self._generate_password_change_link(current_user, user)
        text = jinja2.Template(text_tmpl).render(url=url, name=user.name, email=user.email)
        html = jinja2.Template(html_tmpl).render(url=url, name=user.name, email=user.email)

        ses = AwsUtils.get_client('ses', region_name='us-east-1')
        ses.send_email(
            Source=src_email,
            Destination={
                'ToAddresses': [user.email],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8',
                },
                'Body': {
                    'Text': {
                        'Data': text,
                        'Charset': 'UTF-8',
                    },
                    'Html': {
                        'Data': html,
                        'Charset': 'UTF-8',
                    },
                },
            },
        )

    def create_user(
        self,
        current_user: AuthInfo,
        user: User,
        email_verified: bool = False,
        idp_attributes: dict = None,
        **kwargs,
    ):
        logger.info('Auth0: Creating user', extra={'user': user.entity_id})
        app_metadata = {
            'tenant_id': user.tenant_id,
        }
        app_metadata.update(idp_attributes)

        self._refresh_if_needed()
        try:
            self._handle_token_error(
                lambda: self.auth0.users.create({
                    'email': user.email,
                    'email_verified': email_verified,
                    'name': user.name,
                    'given_name': user.name,
                    # Auth0 doesn't allow empty family_name
                    'family_name': user.family_name or 'na',
                    'app_metadata': app_metadata,
                    # Generate random password and forget about it. First thing the user will do is reset the password.
                    # Auth0 requires that we specify a password, hence we generate one.
                    'password': _generate_password(),
                    'connection': self.connection_id,
                }),
            )
            logger.info('Auth0: User created', extra={'user': user.entity_id})
        except Auth0Error as e:
            logger.error(f'Auth0: Failed to create user in Auth0: {e}')
            if 'PasswordStrengthError' in e.error_code:
                self._password_strength_error(e)
            elif 409 == e.status_code:
                raise ConflictException(f'Auth0 user already exists with email: {user.email}')
            else:
                raise BadRequestException(f'{e.error_code}: {e.message}')

        try:
            self._send_invite_email(current_user, user)
            logger.info('Auth0: Invite email sent', extra={'user': user.entity_id, 'email': user.email})
        except Exception as e:
            logger.error(f'Auth0: Failed to invite user: {e}')
            self.delete_user(current_user, user)
            raise BadRequestException('Failed to create user')

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str],
        **kwargs,
    ):
        logger.info('Auth0: Updating user attributes', extra={'user': user.entity_id})
        user_attributes = dict()
        custom_attributes = dict()
        for k, v in attributes.items():
            if k.startswith('custom:') or k in (_app_metadata_keys):
                custom_attributes[k] = v
            elif k == 'family_name':
                # Auth0 doesn't allow empty family_name
                user_attributes[k] = v or 'na'
            else:
                user_attributes[k] = v

        if custom_attributes:
            user_attributes['app_metadata'] = custom_attributes

        found_user = self._get_user(user)
        self._handle_token_error(lambda: self.auth0.users.update(found_user['user_id'], user_attributes))

    def delete_user(self, current_user: AuthInfo, user: User, **kwargs):
        logger.info('Auth0: Deleting user', extra={'user': user.entity_id})
        try:
            found_user = self._get_user(user)
            self._handle_token_error(lambda: self.auth0.users.delete(found_user['user_id']))
        except NotFoundException:
            # If not found don't raise an error
            logger.info('Auth0: User not found, skipping deletion')

    def change_password(self, current_user: AuthInfo, user: User, new_password: str, **kwargs):
        logger.info('Auth0: Changing password', extra={'user': user.entity_id})
        found_user = self._get_user(user)

        try:
            self._handle_token_error(
                lambda: self.auth0.users.update(
                    found_user['user_id'], {
                        'password': new_password,
                    },
                ),
            )
            logger.info('Auth0: Changed password', extra={'user': user.entity_id})
        except Auth0Error as e:
            if 'PasswordStrengthError' in e.error_code:
                self._password_strength_error(e)
            else:
                raise BadRequestException(f'{e.error_code}: {e.message}')

    def get_user_attributes(self, user: User, **kwargs):
        found_user = self._get_user(user)

        attrs = found_user.get('app_metadata', dict())
        attrs['login_info'] = {
            'last_ip': found_user.get('last_ip'),
            'last_login': found_user.get('last_login'),
            'logins_count': found_user.get('logins_count'),
        }
        return attrs

    def update_or_create_role(self, current_user: AuthInfo, role: Role, **kwargs):
        auth0_role = self._get_role(role.idp_name, False)
        if auth0_role is None:
            logger.info('Auth0: Creating role', extra={'role': role.idp_name})
            self.auth0.roles.create(body={'name': role.idp_name})
            logger.info('Auth0: Created role', extra={'role': role.idp_name})
        else:
            logger.info('Auth0: Updating role', extra={'role': role.idp_name})
            self.auth0.roles.update(auth0_role['id'], body={'name': role.idp_name})
            logger.info('Auth0: Updated role', extra={'role': role.idp_name})

    def delete_role(self, current_user: AuthInfo, role: Role, **kwargs):
        logger.info('Auth0: Deleting role', extra={'role': role.idp_name})

        auth0_role = self._get_role(role.idp_name)
        self.auth0.roles.delete(auth0_role['id'])

        logger.info('Auth0: Deleted role', extra={'role': role.idp_name})

    def update_user_roles(self, current_user: AuthInfo, user: User, roles: List[Role], **kwargs):
        logger.info('Auth0: Updating user roles', extra={'user': user.entity_id, 'roles': [{'id': r.entity_id, 'name': r.name} for r in roles]})
        auth0_user = self._get_user(user)
        # todo add paging for when total results exceeds page size
        auth0_roles = self.auth0.users.list_roles(auth0_user['user_id'], per_page=100)['roles']
        # Filter roles by the "{tenant}_{stage}_" prefix
        all_roles = self.auth0.roles.list(per_page=100, name_filter=f'{current_user.tenant_id}_{STAGE}_')['roles']

        user_base_role = f'{user.tenant_id}_{STAGE}_{TENANT_BASE_ROLE_NAME}'

        add_roles = []
        del_roles = []
        for role in roles:
            role_exists = next((r for r in auth0_roles if r['name'] == f'{role.idp_name}'), None)
            if role_exists is None:
                auth0_role = next((r for r in all_roles if r['name'] == f'{role.idp_name}'), None)
                if auth0_role is not None:
                    add_roles += [auth0_role['id']]

        # if base role exists, and is not assigned, assign it.
        base_role = next((r for r in all_roles if r['name'] == user_base_role), None)
        if (
            base_role is not None
            and next((r for r in auth0_roles if r['name'] == user_base_role), None) is None
        ):
            add_roles += [base_role['id']]

        for auth0_role in auth0_roles:
            # Never delete the base role
            if auth0_role['name'] == user_base_role:
                continue

            role_exists = next((r for r in user.roles if r.idp_name == auth0_role['name']), None)
            if role_exists is None:
                del_roles += [auth0_role['id']]

        if len(add_roles) > 0:
            logger.info('Auth0: Adding roles to user', extra={'user': user.entity_id, 'add_roles': add_roles})
            self.auth0.users.add_roles(auth0_user['user_id'], add_roles)

        if len(del_roles) > 0:
            logger.info('Auth0: Removing roles from user', extra={'user': user.entity_id, 'del_roles': del_roles})
            self.auth0.users.remove_roles(auth0_user['user_id'], del_roles)

        logger.info('Auth0: Updated user roles', extra={'user': user.entity_id})
