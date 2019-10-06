
import redis
from dataclasses import dataclass

from .instance import ClosableInstance
from ..config import ConfigManager
from ..util.helper import parse_boolean

# Source: https://coderwall.com/p/lhyk_w/add-redis-functions-setifhigher-setiflower-zaddifhigher-zaddiflower
_SET_IF_HIGHER_SCRIPT = "local c = tonumber(redis.call('get', KEYS[1])); if c then if tonumber(ARGV[1]) > c then redis.call('set', KEYS[1], ARGV[1]) return tonumber(ARGV[1]) - c else return 0 end else return redis.call('set', KEYS[1], ARGV[1]) end"  # noqa
_SET_IF_LOWER_SCRIPT = "local c = tonumber(redis.call('get', KEYS[1])); if c then if tonumber(ARGV[1]) < c then redis.call('set', KEYS[1], ARGV[1]) return tonumber(ARGV[1]) - c else return 0 end else return redis.call('set', KEYS[1], ARGV[1]) end"   # noqa
_HSET_IF_HIGHER_SCRIPT = "local c = tonumber(redis.call('hget', KEYS[1], ARGV[1])); if c then if tonumber(ARGV[2]) > c then redis.call('hset', KEYS[1], ARGV[1], ARGV[2]) return tonumber(ARGV[2]) - c else return 0 end else return redis.call('hset', KEYS[1], ARGV[1], ARGV[2]) end"
_HSET_IF_LOWER_SCRIPT = "local c = tonumber(redis.call('get', KEYS[1], ARGV[1])); if c then if tonumber(ARGV[2]) < c then redis.call('set', KEYS[1], ARGV[1], ARGV[2]) return tonumber(ARGV[2]) - c else return 0 end else return redis.call('set', KEYS[1], ARGV[1], ARGV[2]) end"   # noqa


def enhance_redis(redis_instance):
    '''
        Registers scripts and adds easy to use functions to the redis_instance object.

        Functions it will add:
            `set_if_higher(key, value)`: Set numeric value only if higher. Returns difference between old and new value, or 'OK' if new.
            `set_if_lower(key, value)`: Set numeric value only if lower. Returns difference between old and new value, or 'OK' if new.
            `hset_if_higher(key, field, value)`: Set numeric value only if higher. Returns difference between old and new value, or 'OK' if new.
            `hset_if_lower(key, field, value)`: Set numeric value only if lower. Returns difference between old and new value, or 'OK' if new.
    '''

    redis_instance.set_if_higher = lambda key, value, client=redis_instance: client.eval(_SET_IF_HIGHER_SCRIPT, 1, key, value)
    redis_instance.set_if_lower = lambda key, value, client=redis_instance: client.eval(_SET_IF_LOWER_SCRIPT, 1, key, value)
    redis_instance.hset_if_higher = lambda key, field, value, client=redis_instance: client.eval(_HSET_IF_HIGHER_SCRIPT, 1, key, field, value)
    redis_instance.hset_if_lower = lambda key, field, value, client=redis_instance: client.eval(_HSET_IF_LOWER_SCRIPT, 1, key, field, value)


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int = 6379
    db: int = 0
    socket_connect_timeout: int = 10
    is_cluster: bool = False
    skip_full_coverage_check: bool = False

    @staticmethod
    def get(tenant_id: str, instance_name: str = None) -> 'RedisConfig':
        key = 'redis'
        if instance_name is not None:
            key += '.' + instance_name

        cm = ConfigManager()
        timeout = cm.get(tenant_id, key + '.socket_connect_timeout')
        redis_config = RedisConfig(
            host=cm.get(tenant_id, key + '.host'),
            port=int(cm.get(tenant_id, key + '.port', 6379)),
            db=int(cm.get(tenant_id, key + '.db', 0)),
            socket_connect_timeout=int(timeout) if timeout is not None else None,
            is_cluster=parse_boolean(cm.get(tenant_id, key + '.is_cluster', 'false')),
            skip_full_coverage_check=parse_boolean(cm.get(tenant_id, key + '.skip_full_coverage_check', 'true'))
        )

        return redis_config


class RedisInstance(ClosableInstance):
    def __init__(
        self,
        tenant_id: str = ConfigManager._DEFAULT_TENANT_ID,
        instance_name: str = None
    ):
        config = RedisConfig.get(tenant_id, instance_name)
        if config.is_cluster:
            raise NotImplementedError("Redis Clusters are not supported.")
        else:
            self.instance = redis.Redis(
                host=config.host,
                port=config.port,
                db=config.db,
                socket_connect_timeout=config.socket_connect_timeout
            )
        enhance_redis(self.instance)

    def get(self):
        return self.instance

    def close(self):
        return True
