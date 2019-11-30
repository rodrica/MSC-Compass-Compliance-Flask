from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.util.aws import get_client

from .base import IdpProvider

if TYPE_CHECKING:
    from ...models import User


class CognitoIdp(IdpProvider):
    def __init__(self):
        self.cognito = get_client('cognito-idp')

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified=False):
        user_pool_id = ConfigManager().get(current_user, 'user_pool_id', raise_if_not_found=True)
        self.cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=user.email,
            TemporaryPassword=password,
            UserAttributes=[
                {'Name': 'email', 'Value': user.email},
                {'Name': 'email_verified ', 'Value': email_verified},
                {'Name': 'name', 'Value': user.name},
                {'Name': 'family_name', 'Value': user.family_name},
                {'Name': 'custom:tenant_id', 'Value': user.tenant_id},
            ],
            DesiredDeliveryMediums=['EMAIL']
        )

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str]
    ):
        user_pool_id = ConfigManager().get(current_user, 'user_pool_id', raise_if_not_found=True)
        self.cognito.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=user.email,
            UserAttributes=[
                {'Name': k, 'Value': v}
                for k, v in attributes.items()
            ]
        )

    def delete_user(self, current_user: AuthInfo, user: User):
        user_pool_id = ConfigManager().get(current_user, 'user_pool_id', raise_if_not_found=True)
        self.cognito.admin_delete_user(
            UserPoolId=user_pool_id,
            Username=user.email,
        )

    def get_user_attributes(self, user: User):
        return NotImplementedError()
