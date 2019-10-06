import fakeredis
import time
from techlock.common.caches import (
    TTLValueWithCompute,
    RedisValueWithCompute,
    DefaultTTLCache,
)


def test_TTLValueWithCompute():
    var = TTLValueWithCompute(lambda: 'world', ttl=5)

    assert var.hits == 0
    assert var.misses == 0

    for x in range(5):
        var.value

    assert var.hits == 4
    assert var.misses == 1

    time.sleep(6)
    var.value
    assert var.hits == 4
    assert var.misses == 2


def test_RedisValueWithCompute():
    rs = fakeredis.FakeStrictRedis()
    var = RedisValueWithCompute(rs, 'hello', lambda: 'world', ttl=5)

    assert var.hits == 0
    assert var.misses == 0

    for x in range(5):
        var.value

    assert var.hits == 4
    assert var.misses == 1

    time.sleep(6)
    var.value
    assert var.hits == 4
    assert var.misses == 2


def test_DefaultTTLCache():
    cache = DefaultTTLCache(lambda x: str(x) + 'world', ttl=5)

    assert cache.hits == 0
    assert cache.misses == 0

    cache['a']
    cache['a']
    cache['a']
    cache['b']

    time.sleep(6)
    cache['a']
    cache['b']
    assert cache.hits == 2
    assert cache.misses == 4
