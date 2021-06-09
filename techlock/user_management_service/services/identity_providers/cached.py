from __future__ import annotations

import logging
from collections import MutableMapping
from typing import TYPE_CHECKING

from techlock.common.config import AuthInfo

from .base import IdpProvider

if TYPE_CHECKING:
    from ...models import Role, User

logger = logging.getLogger(__name__)


class CachedIdp(IdpProvider):
    '''
        Cache wrapper for any IDP
        This method means that the IDP itself is not aware of the cache.
        The cache can be any MutableMapping implementation.

        Will cache the user attributes, and use the cached value if it exists.
        Functions that don't touch the cache are simple pass through.
    '''

    def __init__(
        self,
        wrapped_idp: IdpProvider,
        cache: MutableMapping = dict(),
    ):
        self._wrapped_idp = wrapped_idp
        self._cache = cache

    def create_user(
        self,
        current_user: AuthInfo,
        user: User,
        password: str,
        email_verified: bool = False,
        idp_attributes: dict = None,
        **kwargs,
    ):
        # Create the user
        self._wrapped_idp.create_user(
            current_user,
            user,
            password,
            email_verified,
            idp_attributes,
            **kwargs,
        )

        # Cache the user attributes
        try:
            self._cache[user.entity_id] = self._wrapped_idp.get_user_attributes(user)
        except Exception:
            # Potential for race conditions.
            # Since we're only prepopulating cache, it doesn't really matter if this fails.
            # I just means that it'll have to get if next time
            logger.debug('Cached: Failed to get user attributes after creation. Skipping...')

    def delete_user(
        self,
        current_user: AuthInfo,
        user: User,
        **kwargs,
    ):
        # Delete from cache
        del self._cache[user.entity_id]

        # Delete from IDP
        self._wrapped_idp.delete_user(
            current_user,
            user,
            **kwargs,
        )

    def change_password(
        self,
        current_user: AuthInfo,
        user: User,
        new_password: str,
        **kwargs,
    ):
        # Nothing to do with cache. Pass through
        self._wrapped_idp.change_password(
            current_user,
            user,
            new_password,
            **kwargs,
        )

    def get_user_attributes(
        self,
        user: User,
        **kwargs,
    ):
        # Attempt to get from cache
        attributes = self._cache.get(user.entity_id)

        # If not cached, get actual value and cache it.
        if attributes is None:
            logger.info('User attributes not cached, getting raw data.', extra={'user_id': user.entity_id})
            attributes = self._wrapped_idp.get_user_attributes(user, **kwargs)
            self._cache[user.entity_id] = attributes

        return attributes

    def update_or_create_role(
        self,
        current_user: AuthInfo,
        role: Role,
        **kwargs,
    ):
        # Nothing to do with cache. Pass through
        self._wrapped_idp.update_or_create_role(
            current_user,
            role,
            **kwargs,
        )

    def delete_role(
        self,
        current_user: AuthInfo,
        role: Role,
        **kwargs,
    ):
        # Nothing to do with cache. Pass through
        self._wrapped_idp.delete_role(
            current_user,
            role,
            **kwargs,
        )

    def update_user_roles(
        self,
        current_user: AuthInfo,
        user: User,
        roles: list,
        **kwargs,
    ):
        # Nothing to do with cache. Pass through
        self._wrapped_idp.update_user_roles(
            current_user,
            user,
            roles,
            **kwargs,
        )
