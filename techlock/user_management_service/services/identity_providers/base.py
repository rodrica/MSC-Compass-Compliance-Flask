from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from techlock.common.config import AuthInfo

if TYPE_CHECKING:
    from ...models import User


class IdpProvider():

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified=False, **kwargs):
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
