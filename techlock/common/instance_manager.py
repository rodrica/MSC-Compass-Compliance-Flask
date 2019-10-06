

from collections import defaultdict

from .config import ConfigManager
from .singleton import Singleton
from .instances import (
    ElasticSearchInstance,
    RedisInstance
)

DEFAULT_CLIENT = ConfigManager._DEFAULT_TENANT_ID


class INSTANCE_TYPES:
    REDIS = 'redis',
    ELASTICSEARCH = 'elasticsearch'


_TYPE_REGISTRY = {
    INSTANCE_TYPES.ELASTICSEARCH: ElasticSearchInstance,
    INSTANCE_TYPES.REDIS: RedisInstance
}


class InstanceManager(metaclass=Singleton):
    def __init__(self):
        self._client_instances = defaultdict(lambda: defaultdict(dict))

    def get_instance(self, tenant_id: str = DEFAULT_CLIENT, instance_type: str = None, instance_name: str = None):
        instances = self._client_instances[tenant_id][instance_type]
        if instance_name in instances:
            return instances[instance_name]

        # Don't have an instance yet, create one.
        instance = self.get_new_instance(tenant_id, instance_type, instance_name)
        instances[instance_name] = instance

        return instance

    def get_new_instance(self, tenant_id: str = DEFAULT_CLIENT, instance_type: str = None, instance_name: str = None):
        instance = _TYPE_REGISTRY[instance_type](tenant_id, instance_name).get()

        return instance
