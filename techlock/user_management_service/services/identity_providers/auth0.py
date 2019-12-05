from __future__ import annotations
import logging
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
    'endgame_role',
]


class Auth0Idp(IdpProvider):
    def __init__(self):
        current_user = AuthInfo('Auth0Idp', ConfigManager._DEFAULT_TENANT_ID)
        domain = ConfigManager().get(current_user, 'auth0.domain', raise_if_not_found=True)
        client_id = ConfigManager().get(current_user, 'auth0.client_id', raise_if_not_found=True)
        client_secret = ConfigManager().get(current_user, 'auth0.client_secret', raise_if_not_found=True)
        audience = ConfigManager().get(current_user, 'auth0.audience', raise_if_not_found=True)

        self.connection_id = ConfigManager().get(current_user, 'auth0.connection_id', raise_if_not_found=True)

        get_token = GetToken(domain)
        token = get_token.client_credentials(client_id, client_secret, audience)
        mgmt_api_token = token['access_token']

        self.auth0 = Auth0(domain, mgmt_api_token)

    def _get_user(self, user: User):
        found_users = self.auth0.users_by_email.search_users_by_email(user.email)
        if not found_users:
            logger.error('User not found', extra={'user', user.entity_id})
            raise NotFoundException('User not found')
        elif len(found_users) > 1:
            logger.warn('Found multiple users, expected one. Will use first one.', extra={
                'found_users': found_users
            })

        return found_users[0]

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified: bool = False, idp_attibutes: dict = None):
        app_metadata = {
            'tenant_id': user.tenant_id,
        }
        app_metadata.update(idp_attibutes)

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

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str]
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

    def delete_user(self, current_user: AuthInfo, user: User):
        found_user = self._get_user(user)
        self.auth0.users.delete(found_user['user_id'])

    def change_password(self, current_user: AuthInfo, user: User, new_password: str):
        found_user = self._get_user(user)

        try:
            self.auth0.users.update(found_user['user_id'], {
                'password': new_password,
            })
        except Auth0Error as e:
            if e.error_code == 'PasswordStrengthError':
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
            else:
                raise BadRequestException(f'{e.error_code}: {e.message}')

    def get_user_attributes(self, user: User):
        found_user = self._get_user(user)

        return found_user.get('app_metadata', dict())
