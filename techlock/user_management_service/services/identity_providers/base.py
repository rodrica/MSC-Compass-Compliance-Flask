
from typing import Dict

from techlock.common.config import AuthInfo

from ...models import User


class IdpProvider():

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified=False):
        pass

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str]
    ):
        pass

    def delete_user(self, current_user: AuthInfo, user: User):
        pass
