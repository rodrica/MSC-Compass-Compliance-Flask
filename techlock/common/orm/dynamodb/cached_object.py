import logging

from techlock.common.api import PageableResponse
from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.instance_manager import InstanceManager, INSTANCE_TYPES
from techlock.common.util.helper import parse_boolean

from .persisted_object import PersistedObject

logger = logging.getLogger('persisted_object')


class CachedPersistedObject(PersistedObject):

    @classmethod
    def _should_use_cache(cls, auth_info: AuthInfo):
        return not(parse_boolean(ConfigManager().get(auth_info.tenant_id, 'no_cache')))

    @classmethod
    def _get_cache_key(cls, tenant_id: str):
        return '{}:{}'.format(
            tenant_id,
            cls._get_table_name()
        )

    def save(self, auth_info: AuthInfo):
        # Persist
        resp = super().save(auth_info)

        if self._should_use_cache(auth_info):
            # Cache
            redis = InstanceManager().get_instance(auth_info.tenant_id, INSTANCE_TYPES.REDIS)
            redis.hset(self._get_cache_key(self.tenant_id), self.entity_id, self.asjson())

        return resp

    def delete(self, auth_info: AuthInfo):
        # Persist
        resp = super().delete(auth_info)

        if self._should_use_cache(auth_info):
            # Cache
            redis = InstanceManager().get_instance(auth_info.tenant_id, INSTANCE_TYPES.REDIS)
            redis.hdel(self._get_cache_key(self.tenant_id), self.entity_id)

        return resp

    @classmethod
    def get(cls, auth_info: AuthInfo, entity_id):
        should_use_cache = cls._should_use_cache(auth_info)
        if should_use_cache:
            # Attempt to get from cache
            redis = InstanceManager().get_instance(auth_info.tenant_id, INSTANCE_TYPES.REDIS)
            cached_json = redis.hget(cls._get_cache_key(auth_info.tenant_id), entity_id)
            cached_obj = None
            if cached_json:
                try:
                    cached_obj = cls.from_json(cached_json)
                except Exception as e:
                    logger.warn("Failed to deserialize %s from '%s'", cls.__name__, cached_json)
                    logger.debug(e, exc_info=True)

            if cached_obj:
                return cached_obj

        # Could not get cached object, fall back to actual persistence store
        obj = super().get(auth_info, entity_id)
        # If not found in cache, but we want to use cache, store it in cache
        if obj and should_use_cache:
            redis.hset(cls._get_cache_key(auth_info.tenant_id), entity_id, obj.asjson())
        return obj

    @classmethod
    def get_all(
        cls,
        auth_info: AuthInfo,
        ids=None,
        limit=100,
        start_key=None,
        created_by_user_id=None,
        additional_attrs=None
    ) -> PageableResponse:
        should_use_cache = cls._should_use_cache(auth_info) and additional_attrs is None and start_key is None
        # only use cache if there are is no start_key and no additional_attrs
        if should_use_cache:
            # Attempt to get from cache
            redis = InstanceManager().get_instance(auth_info.tenant_id, INSTANCE_TYPES.REDIS)
            cached_jsons = redis.hgetall(cls._get_cache_key(auth_info.tenant_id))
            cached_objs = []
            result = []
            if cached_jsons:
                # parse json
                for cached_json in cached_jsons.values():
                    try:
                        cached_objs.append(cls.from_json(cached_json))
                    except Exception as e:
                        logger.warn("Failed to deserialize %s from '%s'", cls.__name__, cached_json)
                        logger.debug(e, exc_info=True)

                        # Batch is sour, throw it all out
                        cached_objs = []
                        break

                for obj in sorted(cached_objs, key=lambda k: k.entity_id):
                    if ids and obj.entity_id not in ids:
                        continue
                    if created_by_user_id and obj.created_by != created_by_user_id:
                        continue

                    result.append(obj)

            if result:
                response = PageableResponse(
                    items=result
                )
                return response

        # Could not get cached objects, fall back to actual persistence store
        resp = super().get_all(auth_info, ids=ids, limit=limit, start_key=start_key, created_by_user_id=created_by_user_id, additional_attrs=additional_attrs)
        # If not found in cache, but we want to use cache, store it in cache
        if resp.items and should_use_cache:
            for obj in resp.items:
                redis.hset(cls._get_cache_key(auth_info.tenant_id), obj.entity_id, obj.asjson())
        return resp
