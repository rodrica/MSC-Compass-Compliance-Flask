from __future__ import unicode_literals
# from builtins import str  # Uncomment if you're using str(). Need this for Python 2 & 3 compatibility
import json
from uuid import UUID

from techlock.common.util.helper import minify_string
from techlock.common.util.serializers import JSONEncoder


# pylint: disable=E0202, no-self-use
class SortedDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        new_obj = dict()
        for k, v in obj.items():
            if isinstance(v, list) and len(v) != 0:
                if isinstance(v[0], dict):
                    # Python3's sorted function doesn't handle dicts, so here we take the list of dicts, and sort them by their json string.
                    # This allows us to ignore the order when comparing list of dicts
                    tmp_dict = dict((json.dumps(d), d) for d in v)
                    sorted_keys = sorted(tmp_dict.keys())
                    new_obj[k] = [tmp_dict[k] for k in sorted_keys]
                else:
                    new_obj[k] = sorted(v)
            else:
                new_obj[k] = v
        return new_obj


def assert_valid_uuid4(uuid_string):
    '''
    Validate that a UUID string is in
    fact a valid uuid4.
    Happily, the uuid module does the actual
    checking for us.
    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    '''

    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False

    # If the uuid_string is a valid hex code,
    # but an invalid uuid4,
    # the UUID.__init__ will convert it to a
    # valid uuid4. This is bad for validation purposes.

    return val.hex == uuid_string


def assert_string_minified(actual, expected, minify_comma=True):
    '''
        Asserts that strings are identical, and ignore whitespace differences.
        This is very useful for comparing generated queries for example, where you
        might want to have a human readable version in your test file.

        Args:
            actual (str):           Actual string to compare against expected.
            expected (str):         The string we expect actual to be equal to.
            minify_comma (bool):    Should we minify commas? e.g.: 'a, b' -> 'a,b'
    '''
    actual = minify_string(actual, minify_comma=minify_comma)
    expected = minify_string(expected, minify_comma=minify_comma)

    assert actual == expected


def assert_as_json(actual, expected):
    '''
        Asserts that the json is identical.
        This can be very helpful when comparing dict vs defaultdict, or list vs set.
    '''
    actual = json.loads(json.dumps(actual, cls=JSONEncoder, sort_keys=True), cls=SortedDecoder)
    expected = json.loads(json.dumps(expected, cls=JSONEncoder, sort_keys=True), cls=SortedDecoder)

    if isinstance(actual, list):
        actual = sorted(actual)
    if isinstance(expected, list):
        expected = sorted(expected)

    assert actual == expected
