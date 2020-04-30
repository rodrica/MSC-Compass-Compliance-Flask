import logging
from redis import Redis
from redis.connection import to_bool, URL_QUERY_ARGUMENT_PARSERS
from urllib.parse import parse_qs, urlparse
from techlock.common import ConfigManager
from techlock.common.caches import RedisStore

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
    cache_url: str = None,
):
    if cached is None:
        cached = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.cached')
    if cache_url is None:
        cache_url = ConfigManager().get(ConfigManager._DEFAULT_TENANT_ID, 'idp.cache_url')
    # If cached is not set, but the url is. Enable cache. This will honor cached = False.
    if cached is None and cache_url:
        cached = True

    return cached, cache_url


def _get_cache(cache_url, idp_instance):
    cache = dict()
    if cache_url:
        url = urlparse(cache_url)
        if url.scheme == 'tl-redis-store':
            logger.info('Creating RedisStore.')
            # Get query params as dict from query string
            url_options = {k: v[0] for k, v in parse_qs(url.query).items()}
            # Get all redis kwargs, and convert if needed. Get with lambda is more readable than if else.
            redis_kwargs = {
                k: URL_QUERY_ARGUMENT_PARSERS.get(k, lambda x: x)(v)
                for k, v in url_options
                if k not in ('key_prefix', 'ttl')
            }
            redis = Redis(
                host=url.hostname,
                port=int(url.port or 6379),
                password=url.password,
                db=int(url.path.replace('/', '') or 0),
                **redis_kwargs
            )

            cache = RedisStore(
                redis,
                key_prefix=url_options.get('key_prefix', idp_instance.__class__.__name__),
                ttl=url_options.get('ttl', 3600),
            )
        else:
            raise ValueError(f'Invalid scheme provided: {url.scheme}')

    return cache


def get_idp(
    idp_name: str = None,
    cached: bool = None,
    cache_url: str = None,
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
    cached, cache_url = _get_defaulted_cache_vars(cached, cache_url)
    if cached:
        cache = _get_cache(cache_url, idp_instance)
        idp_instance = CachedIdp(idp_instance, cache=cache)

    _idp_cache[idp_name] = idp_instance
    return idp_instance
