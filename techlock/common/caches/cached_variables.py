import json
import time
from cachetools import Cache, TTLCache


class TTLValueWithCompute:
    '''
        Holds a value with a ttl.
        If the value has expired, calls the default_factory function to set it again.

        Usage:
            >> cached_value = TTLValueWithCompute(lamba: 'world', ttl=60)
            >> cached_value.value
            'world'
            >> cached_value.value
            'world'
            >> sleep(65)
            >> cached_value.value
            'world'
            >> cached.hits
            1
            >> cached_value.misses
            2
    '''
    def __init__(self, default_factory, ttl=60):
        self._value = None
        self.compute_time = 0
        self.default_factory = default_factory
        self.ttl = ttl
        self._hits = 0
        self._misses = 0

    @property
    def value(self):
        # TTL expired. Compute and Set
        if self.compute_time + self.ttl < time.time():
            self.compute_time = time.time()
            self._value = self.default_factory()
            self._misses += 1
        else:
            self._hits += 1
        return self._value

    @value.setter
    def value(self, _value):
        self.compute_time = time.time()
        self._value = _value

    @property
    def hits(self):
        return self._hits

    @property
    def misses(self):
        return self._misses


class RedisValueWithCompute:
    '''
        If redis does not have the value, calls the default_factory function to set it again.

        Usage:
            >> cached_value = RedisValueWithCompute(redis_instance, lamba: 'world', ttl=60)
            >> cached_value.value
            'world'
            >> cached_value.value
            'world'
            >> sleep(65)
            >> cached_value.value
            'world'
            >> cached.hits
            1
            >> cached_value.misses
            2
    '''
    def __init__(self, redis_instance, key, default_factory, ttl=60, store_as_json=False):
        self.redis_instance = redis_instance
        self.key = key
        self.default_factory = default_factory
        self.ttl = ttl
        self.store_as_json = store_as_json
        self._hits = 0
        self._misses = 0

    @property
    def value(self):
        _value = self.redis_instance.get(self.key)
        # None, so doesn't exist in Redis. Compute and Set.
        if _value is None:
            _value = self.default_factory()
            self._set(_value)
            self._misses += 1
        else:
            self._hits += 1
        if self.store_as_json:
            _value = json.loads(_value)
        return _value

    @value.setter
    def value(self, _value):
        self._set(_value)

    def _set(self, _value):
        if self.store_as_json:
            _value = json.dumps(_value)

        self.redis_instance.set(self.key, _value, ex=self.ttl)

    @property
    def hits(self):
        return self._hits

    @property
    def misses(self):
        return self._misses


class DefaultTTLCache(TTLCache):
    '''
        Extends the TTLCache with defaultdict behavior
        https://cachetools.readthedocs.io/en/latest/#cachetools.TTLCache
    '''
    def __init__(self, default_factory, max_size=1024, ttl=60, pass_key=True, set_none=True):
        '''
            Args:
                default_factory: Function or lambda to call if the value doesn't exist or is expired
                max_size: The maximum size of the cache.
                ttl: The time-to-live value of the cache’s items in seconds.
                pass_key: Should we pass the key to the default_factory?
                set_none: If the factory return `None` should we still set it? (If set, the None value will have the normal ttl)
        '''
        super().__init__(max_size, ttl)
        self.default_factory = default_factory
        self.pass_key = pass_key
        self.set_none = set_none
        self._hits = 0
        self._misses = 0

    def __missing__(self, key):
        if self.pass_key:
            value = self.default_factory(key)
        else:
            value = self.default_factory()
        if value is not None or self.set_none:
            TTLCache.__setitem__(self, key, value)
        return value

    def __getitem__(self, key, cache_getitem=Cache.__getitem__):
        miss = False
        try:
            link = self._TTLCache__getlink(key)
        except KeyError:
            miss = True
            expired = False
        else:
            expired = link.expire < self._TTLCache__timer()
        if expired:
            miss = True
            value = self.__missing__(key)
        else:
            value = cache_getitem(self, key)
        # If we only do the count in the above `if expired.. else` block, then we'd count never initialized values as a hits
        if miss:
            self._misses += 1
        else:
            self._hits += 1
        return value

    @property
    def hits(self):
        return self._hits

    @property
    def misses(self):
        return self._misses
