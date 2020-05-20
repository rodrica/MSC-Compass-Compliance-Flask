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
    from ...models import User

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
        # Expire 10 second earlier - This prevents the scenario where the request expires after we checked.
        return self.token_expiration - 10 >= int(time.time())

    def _refresh_if_needed(self):
        try:
            if self._is_refresh_needed():
                self._refresh_token()
        except Exception as e:
            logger.error(f'Failed to refresh token. Error={e}')

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
        found_users = self.auth0.users.list(q=f'identities.connection: "{self.connection_id}" AND email: "{user.email}"')
        total_found_users = found_users['total']
        if not total_found_users:
            logger.error('User not found', extra={'user': user.entity_id})
            raise NotFoundException('User not found')
        elif total_found_users > 1:
            logger.warn('Found multiple users, expected one. Will use first one.', extra={
                'found_users': found_users
            })

        return found_users['users'][0]

    def create_user(
        self,
        current_user: AuthInfo,
        user: User,
        password: str,
        email_verified: bool = False,
        idp_attributes: dict = None,
        **kwargs,
    ):
        app_metadata = {
            'tenant_id': user.tenant_id,
        }
        app_metadata.update(idp_attributes)

        self._refresh_if_needed()
        try:
            self.auth0.users.create({
                'email': user.email,
                'email_verified': email_verified,
                'name': user.name,
                'given_name': user.name,
                'family_name': user.family_name,
                'app_metadata': app_metadata,
                'password': password,
                'connection': self.connection_id,
            })
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
        user_attributes = dict()
        custom_attributes = dict()
        for k, v in attributes.items():
            if k.startswith('custom:') or k in (_app_metadata_keys):
                custom_attributes[k] = v
            else:
                user_attributes[k] = v

        if custom_attributes:
            user_attributes['app_metadata'] = custom_attributes

        found_user = self._get_user(user)
        self.auth0.users.update(found_user['user_id'], user_attributes)

    def delete_user(self, current_user: AuthInfo, user: User, **kwargs):
        try:
            found_user = self._get_user(user)
            self.auth0.users.delete(found_user['user_id'])
        except NotFoundException:
            # If not found don't raise an error
            logger.info('User not found, skipping deletion')

    def change_password(self, current_user: AuthInfo, user: User, new_password: str, **kwargs):
        found_user = self._get_user(user)

        try:
            self.auth0.users.update(found_user['user_id'], {
                'password': new_password,
            })
        except Auth0Error as e:
            if 'PasswordStrengthError' in e.error_code:
                self._password_strength_error(e)
            else:
                raise BadRequestException(f'{e.error_code}: {e.message}')

    def get_user_attributes(self, user: User, **kwargs):
        found_user = self._get_user(user)

        return found_user.get('app_metadata', dict())
