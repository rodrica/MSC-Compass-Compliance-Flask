import logging
from typing import Dict

from techlock.common.config import AuthInfo

from .base import IdpProvider
from ...models import User

logger = logging.getLogger(__name__)


class MockIdp(IdpProvider):

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified=False):
        logger.info("create_user")
        pass

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str]
    ):
        logger.info("update_user_attributes")

    def delete_user(self, current_user: AuthInfo, user: User):
        logger.info("delete_user")

    def change_password(self, current_user: AuthInfo, user: User, new_password: str):
        logger.info("change_password")
