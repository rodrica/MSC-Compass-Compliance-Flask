from __future__ import annotations
import logging
from typing import Dict, TYPE_CHECKING

from techlock.common.config import AuthInfo

from .base import IdpProvider

if TYPE_CHECKING:
    from ...models import User

logger = logging.getLogger(__name__)


class MockIdp(IdpProvider):

    def create_user(self, current_user: AuthInfo, user: User, password: str, email_verified=False, **kwargs):
        logger.info("create_user")
        pass

    def update_user_attributes(
        self,
        current_user: AuthInfo,
        user: User,
        attributes: Dict[str, str],
        **kwargs
    ):
        logger.info("update_user_attributes")

    def delete_user(self, current_user: AuthInfo, user: User, **kwargs):
        logger.info("delete_user")

    def change_password(self, current_user: AuthInfo, user: User, new_password: str, **kwargs):
        logger.info("change_password")

    def get_user_attributes(self, user: User, **kwargs):
        logger.info("get_user_attributes")

    def create_role(self, current_user: AuthInfo, role: Role):
        logger.info("create_role")

    def update_or_create_role(self, current_user: AuthInfo, role: Role, role_name: str):
        logger.info("update_or_create_role")

    def delete_role(self, current_user: AuthInfo, role: Role):
        logger.info("delete_role")
