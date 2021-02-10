from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from techlock.common.config import AuthInfo

if TYPE_CHECKING:
    from ...models import Role, User


class IdpProvider():

    def create_user(
        self,
        current_user: AuthInfo,
        user: User,
        password: str,
        email_verified=False,
        **kwargs
    ):
        pass

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str],
        **kwargs
    ):
        pass

    def delete_user(self, current_user: AuthInfo, user: User, **kwargs):
        pass

    def change_password(self, current_user: AuthInfo, user: User, **kwargs):
        pass

    def get_user_attributes(self, user: User, **kwargs):
        pass

    def update_or_create_role(self, current_user: AuthInfo, role: Role):
        pass

    def delete_role(self, current_user: AuthInfo, role: Role):
        pass

    def update_user_roles(self, current_user: AuthInfo, user: User, roles: list):
        pass
