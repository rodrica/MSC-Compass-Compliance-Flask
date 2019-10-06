'''
    Holds our Tavern validators
    https://taverntesting.github.io/examples.html#external-functions
'''

from dateutil.parser import parse

from .helpers import assert_as_json, assert_valid_uuid4


def validate_json(response, expected):
    '''
        Validates the json but ignores array orders
    '''
    actual = response.json()

    assert_as_json(actual, expected)


def _validate_persisted_object(actual, expected, has_previous_version=False):
    '''
        Validates the persistent object.
        Since we use UUIDs, validate validity by default instead of exact value.
        Compare Dates via '%Y-%m-%dT%H-%M-%S' format if provided.
    '''
    print(actual)
    if 'entity_id' not in expected:
        assert_valid_uuid4(actual['entity_id'])
        actual.pop('entity_id', None)
    if 'version' not in expected:
        assert_valid_uuid4(actual['version'])
        actual.pop('version', None)
    if 'previous_version' not in expected:
        if has_previous_version:
            assert_valid_uuid4(actual['previous_version'])
        assert actual['previous_version'] is None
        actual.pop('previous_version', None)
    if 'created_on' in expected:
        actual_created = parse(actual['created_on']).strptime('%Y-%m-%dT%H-%M-%S')
        assert actual_created == expected['created_on']
    if 'changed_on' in expected:
        actual_changed = parse(actual['changed_on']).strptime('%Y-%m-%dT%H-%M-%S')
        assert actual_changed == expected['changed_on']

    actual.pop('created_on', None)
    actual.pop('changed_on', None)
    for k, v in dict(actual).items():
        if isinstance(v, dict) and 'entity_id' in v and k in expected and isinstance(expected[k], dict):
            _validate_persisted_object(v, expected[k])
            actual.pop(k, None)
            expected.pop(k, None)

    assert_as_json(actual, expected)


def validate_persisted_object(response, expected, has_previous_version=False):
    '''
        Validates persisted object or list of objects
    '''
    actual = response.json()
    if 'items' in actual and 'items' in expected:
        actual_len = len(actual['items'])
        expected_len = len(expected['items'])
        assert actual_len == expected_len, "{} == {}".format(actual_len, expected_len)

        for actual_item, expected_item in zip(sorted(actual['items'], key=lambda i: i['entity_id']), sorted(expected['items'], key=lambda i: i['entity_id'])):
            _validate_persisted_object(actual_item, expected_item, has_previous_version)

        actual.pop('items', None)
        expected.pop('items', None)
        assert_as_json(actual, expected)
    else:
        _validate_persisted_object(actual, expected, has_previous_version)
