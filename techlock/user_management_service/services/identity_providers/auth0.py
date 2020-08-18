from __future__ import annotations
import jwt
import logging
import time
from typing import Dict, TYPE_CHECKING
from auth0.v3.authentication import GetToken
from auth0.v3.exceptions import Auth0Error
from auth0.v3.management import Auth0

from techlock.common.api import BadRequestException, NotFoundException
from techlock.common.config import AuthInfo, ConfigManager

from .base import IdpProvider
if TYPE_CHECKING:
    from ...models import User, Role

logger = logging.getLogger(__name__)

_app_metadata_keys = [
]


class Auth0Idp(IdpProvider):
    def __init__(self):
        current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
        self.connection_id = ConfigManager().get(current_user, 'auth0.connection_id', raise_if_not_found=True)

        self._refresh_token()

    def _refresh_token(self):
        current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
        domain = ConfigManager().get(current_user, 'auth0.domain', raise_if_not_found=True)
        client_id = ConfigManager().get(current_user, 'auth0.client_id', raise_if_not_found=True)
        client_secret = ConfigManager().get(current_user, 'auth0.client_secret', raise_if_not_found=True)
        audience = ConfigManager().get(current_user, 'auth0.audience', raise_if_not_found=True)

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

        logger.debug('Checking if Auth0 token refresh is needed.', extra={
            'token_expiration': self.token_expiration,
            'time': now,
            'is_needed': is_refresh_needed
        })

        return is_refresh_needed

    def _refresh_if_needed(self):
        try:
            if self._is_refresh_needed():
                self._refresh_token()
        except Exception as e:
            logger.error(f'Failed to refresh token. Error={e}')

    def _handle_token_error(self, callback):
        '''
            Handle token expired error and refresh.
            While calling `self._refresh_if_needed()` before should fix it. This just handles the odd case that it didn't.
        '''
        try:
            return callback()
        except Auth0Error as e:
            if 'expired token' in e.message.lower():
                logger.error('Token expired, refreshing and trying again.')
                self._refresh_token()
                return callback()
            else:
                raise

    def _password_strength_error(self, e):
        conn_options = self.auth0.connections.get(self.connection_id)['options']

        raise BadRequestException('Password is too weak.', payload={
            'rules': {
                'min_length': conn_options['password_complexity_options']['min_length'],
                'history_size': conn_options['password_history']['size'],
                'no_personal_info': conn_options['password_no_personal_info']['enabled'],
                'must_incl_number': conn_options['passwordPolicy'] in ('fair', 'good', 'excellent'),
                'must_incl_special': conn_options['passwordPolicy'] in ('good', 'excellent'),
                'no_consecutive': conn_options['passwordPolicy'] == 'excellent',
            }
        })

    def _get_user(self, user: User):
        self._refresh_if_needed()
        found_users = self._handle_token_error(lambda: self.auth0.users.list(
            q=f'identities.connection: "{self.connection_id}" AND email: "{user.email}"'
        ))
        total_found_users = found_users['total']
        if not total_found_users:
            logger.error('User not found', extra={'user': user.entity_id})
            raise NotFoundException('User not found')
        elif total_found_users > 1:
            logger.warn('Found multiple users, expected one. Will use first one.', extra={
                'found_users': found_users
            })

        return found_users['users'][0]

    def _get_role(self, role_name: str, throw_if_not_found: bool = True):
        self._refresh_if_needed()
        roles = self.auth0.roles.list(name_filter=role_name)['roles']
        if len(roles) > 1:
            logger.warn('Found multiple roles, expected one. Will use first one.', extra={
                'roles': roles
            })

        for role in roles:
            if role['name'] == role_name:
                return role

        if throw_if_not_found:
            logger.error(f'Role {role_name} not found')
            raise NotFoundException('Role not found')
        else:
            return None

    def create_user(
        self,
        current_user: AuthInfo,
        user: User,
        password: str,
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
                    'password': password,
                    'connection': self.connection_id,
                })
            )
            logger.info('Auth0: User created', extra={'user': user.entity_id})
        except Auth0Error as e:
            logger.error(f'Failed to create user in Auth0: {e}')
            if 'PasswordStrengthError' in e.error_code:
                self._password_strength_error(e)
            else:
                raise BadRequestException(f'{e.error_code}: {e.message}')

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str],
        **kwargs
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
            logger.info('User not found, skipping deletion')

    def change_password(self, current_user: AuthInfo, user: User, new_password: str, **kwargs):
        logger.info('Auth0: Changing password', extra={'user': user.entity_id})
        found_user = self._get_user(user)

        try:
            self._handle_token_error(lambda: self.auth0.users.update(found_user['user_id'], {
                'password': new_password,
            }))
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
            'logins_count': found_user.get('logins_count')
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

    def update_user_roles(self, current_user: AuthInfo, user: User, roles: list, **kwargs):
        logger.info('Auth0: Updating user roles', extra={'user': user.entity_id})
        auth0_user = self._get_user(user)
        auth0_roles = self.auth0.users.list_roles(auth0_user['user_id'])['roles']
        all_roles = self.auth0.roles.list()['roles']

        add_roles = []
        del_roles = []
        for role in roles:
            role_exists = next((x for x in auth0_roles if x['name'] == f'{role.idp_name}'), None)
            if role_exists is None:
                auth0_role = next((x for x in all_roles if x['name'] == f'{role.idp_name}'), None)
                if auth0_role is not None:
                    add_roles += [auth0_role['id']]

        for auth0_role in auth0_roles:
            role_exists = next((x for x in user.roles if f'{x.tenant_id}_{x.name}' == auth0_role['name']), None)
            if role_exists is None:
                del_roles += [auth0_role['id']]

        if len(add_roles) > 0:
            self.auth0.users.add_roles(auth0_user['user_id'], add_roles)

        if len(del_roles) > 0:
            self.auth0.users.remove_roles(auth0_user['user_id'], del_roles)

        logger.info('Auth0: Updated user roles', extra={'user': user.entity_id})
