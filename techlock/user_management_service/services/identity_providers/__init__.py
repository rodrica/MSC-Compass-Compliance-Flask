import logging
from redis import Redis
from redis.connection import to_bool, URL_QUERY_ARGUMENT_PARSERS
from urllib.parse import parse_qs, urlparse
from techlock.common import ConfigManager
from techlock.common.caches import RedisStore
from techlock.common.instance_manager import InstanceManager, INSTANCE_TYPES

from .auth0 import Auth0Idp
from .base import IdpProvider
from .cached import CachedIdp
from .cognito import CognitoIdp
from .mock import MockIdp

logger = logging.getLogger(__name__)

_idp_map = {
    'AUTH0': Auth0Idp,
    'COGNITO': CognitoIdp,
    'MOCK': MockIdp,
}

# Local runtime cache of ids by name.
_idp_cache = dict()


def _get_defaulted_cache_vars(
    cached: bool = None,
    cache_type: str = None,
):
    if cached is None:
        cached = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.cached')
    if cache_type is None:
        cache_type = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.cache_type')
    # If cached is not set, but the url is. Enable cache. This will honor cached = False.
    if cached is None and cache_type:
        cached = True

    return cached, cache_type


def _get_cache(cache_type, idp_instance):
    cache = dict()
    if cache_type:
        if cache_type == 'redis':
            logger.info('Creating RedisStore.')
            cache_ttl = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.cache_ttl', 3600)
            redis = InstanceManager().get_instance(instance_type=INSTANCE_TYPES.REDIS, instance_name='idp')

            cache = RedisStore(
                redis,
                key_prefix=idp_instance.__class__.__name__,
                ttl=cache_ttl,
            )
        elif cache_type != 'dict':
            raise ValueError(f'Invalid scheme provided: {cache_type}')

    return cache


def get_idp(
    idp_name: str = None,
    cached: bool = None,
    cache_type: str = None,
) -> IdpProvider:
    # Get the IDP name, default to MOCK
    if idp_name is None:
        idp_name = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.name', 'MOCK')

    if idp_name in _idp_cache:
        logger.debug(f'IDP cache hit for {idp_name}')
        return _idp_cache[idp_name]

    logger.info(f'IDP cache miss for {idp_name}')

    # Get the actual IDP instance
    idp_class = _idp_map.get(idp_name.upper())
    if idp_class is None:
        raise NotImplementedError("No idp with name '{}' is implemented".format(idp_name))
    idp_instance = idp_class()

    # Cache the IDP if configured
    cached, cache_type = _get_defaulted_cache_vars(cached, cache_type)
    if cached:
        cache = _get_cache(cache_type, idp_instance)
        idp_instance = CachedIdp(idp_instance, cache=cache)

    _idp_cache[idp_name] = idp_instance
    return idp_instance
