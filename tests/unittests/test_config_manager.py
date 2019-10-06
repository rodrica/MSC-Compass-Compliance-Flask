import boto3
import os
import time
from moto import mock_dynamodb2

from techlock.common import ConfigManager, Singleton
os.environ['AWS_ACCESS_KEY_ID'] = 'key_id'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'access_key'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

tenant_id = 'test_client'
version = '00000000000000000000000000000000'


@mock_dynamodb2
def test_ConfigManager():
    cm = ConfigManager()
    assert cm.stage == 'dev'
    assert cm.table_name == 'mss.dev.config'

    # Now remove singleton instance so we can reinitalize it
    Singleton._instances.pop(ConfigManager)

    os.environ['STAGE'] = 'test'
    cm = ConfigManager()
    assert cm.stage == 'test'
    assert cm.table_name == 'mss.test.config'
    # Now remove singleton instance so we can reinitalize it
    Singleton._instances.pop(ConfigManager)


@mock_dynamodb2
def test_static_ConfigManager():
    cm = ConfigManager()
    cm.static_config['test'] = 'success'
    cm.static_config['redis'] = {'host': 'redis.com', 'port': 6379, 'db': 0}

    value = cm.get(tenant_id, 'test')
    assert value == 'success'

    value = cm.get(tenant_id, 'redis')
    assert value == {'host': 'redis.com', 'port': 6379, 'db': 0}

    value = cm.get(tenant_id, 'redis.host')
    assert value == 'redis.com'

    value = cm.get(tenant_id, 'redis.port')
    assert value == 6379
    # Now remove singleton instance so we can reinitalize it
    Singleton._instances.pop(ConfigManager)


@mock_dynamodb2
def test_os_ConfigManager():
    cm = ConfigManager()
    os.environ['test'] = 'success'
    os.environ['TEST2'] = 'success2'
    os.environ['REDIS_HOST'] = 'redis.com'

    value = cm.get(tenant_id, 'test')
    assert value == 'success'
    value = cm.get(tenant_id, 'test2')
    assert value == 'success2'
    value = cm.get(tenant_id, 'redis.host')
    assert value == 'redis.com'
    # Now remove singleton instance so we can reinitalize it
    Singleton._instances.pop(ConfigManager)
    os.environ.pop('test')
    os.environ.pop('TEST2')
    os.environ.pop('REDIS_HOST')


@mock_dynamodb2
def test_dynamodb_ConfigManager():
    cm = ConfigManager(cache_ttl=5)

    ddb = boto3.client('dynamodb')
    ddb.create_table(
        TableName=cm.table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'tenant_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'version',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'tenant_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'version',
                'KeyType': 'RANGE'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    ddb.put_item(
        TableName=cm.table_name,
        Item={
            'tenant_id': {'S': cm._DEFAULT_TENANT_ID},
            'version': {'S': version},
            'test': {'S': 'default_success'},
            'redis': {'M': {'host': {'S': 'default.redis.com'}, 'port': {'N': '6379'}, 'db': {'N': '0'}}}
        }
    )
    value = cm.get(tenant_id, 'test')
    assert value == 'default_success'
    value = cm.get(tenant_id, 'redis.host')
    assert value == 'default.redis.com'
    time.sleep(6)  # Wait for `tenant_id = None` to expire

    ddb.put_item(
        TableName=cm.table_name,
        Item={
            'tenant_id': {'S': tenant_id},
            'version': {'S': version},
            'test': {'S': 'success'},
            'redis': {'M': {'host': {'S': 'redis.com'}, 'port': {'N': '6379'}, 'db': {'N': '0'}}}
        }
    )
    value = cm.get(tenant_id, 'test')
    assert value == 'success'
    value = cm.get(tenant_id, 'redis.host')
    assert value == 'redis.com'
    value = cm.get(tenant_id, 'redis.port')
    assert value == 6379
    # Now remove singleton instance so we can reinitalize it
    Singleton._instances.pop(ConfigManager)


@mock_dynamodb2
def test_precedence_ConfigManager():
    cm = ConfigManager(cache_ttl=5)
    cm.static_config['test'] = 'static_success'
    os.environ['test'] = 'os_env_success'

    ddb = boto3.client('dynamodb')
    ddb.create_table(
        TableName=cm.table_name,
        AttributeDefinitions=[
            {
                'AttributeName': 'tenant_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'version',
                'AttributeType': 'S'
            }
        ],
        KeySchema=[
            {
                'AttributeName': 'tenant_id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'version',
                'KeyType': 'RANGE'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    ddb.put_item(
        TableName=cm.table_name,
        Item={
            'tenant_id': {'S': cm._DEFAULT_TENANT_ID},
            'version': {'S': version},
            'test': {'S': 'default_success'}
        }
    )
    ddb.put_item(
        TableName=cm.table_name,
        Item={
            'tenant_id': {'S': tenant_id},
            'version': {'S': version},
            'test': {'S': 'success'}
        }
    )

    value = cm.get(tenant_id, 'test')
    assert value == 'static_success'
    cm.static_config.pop('test')

    value = cm.get(tenant_id, 'test')
    assert value == 'os_env_success'
    os.environ.pop('test')

    value = cm.get(tenant_id, 'test')
    assert value == 'success'

    time.sleep(6)  # Wait for cache to expire
    ddb.delete_item(
        TableName=cm.table_name,
        Key={
            'tenant_id': {'S': tenant_id},
            'version': {'S': version}
        }
    )
    value = cm.get(tenant_id, 'test')
    assert value == 'default_success'
