import boto3
import os
import pytest

from techlock.common.api.flask import create_flask
from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.instance_manager import InstanceManager, INSTANCE_TYPES
from techlock.common.orm.sqlalchemy import db
from techlock.common.util.aws import get_client
from techlock.common.util.helper import supress
from techlock.user_management_service.models import (
    Department,
    Office,
    Role,
    Tenant,
    User
)

flask_wrapper = create_flask(__name__, enable_jwt=False, audience='user-management')


def _flush_local_dynamodb(create=True):
    if os.name == 'nt':
        raise Exception("Can't run on Windows. Bug in `time` module causes `dynamodb.create_table` to fail.")

    print('endpoint_url: %s' % os.environ['DYNAMODB_ENDPOINT_URL'])
    ddb = boto3.client('dynamodb', endpoint_url=os.environ['DYNAMODB_ENDPOINT_URL'])
    tables = [
        ConfigManager().table_name,
        # Department._get_table_name(),
        # Office._get_table_name(),
        # Role._get_table_name(),
        # Tenant._get_table_name(),
        # User._get_table_name()
    ]

    for table in tables:
        # Supress because we don't care if the table doesn't exist
        with supress(Exception):
            print('Deleting table: %s' % table)
            ddb.delete_table(TableName=table)

        if create:
            print('Creating table: %s' % table)

            hash_key = 'tenant_id' if table == ConfigManager().table_name else 'entity_id'
            ddb.create_table(
                TableName=table,
                KeySchema=[
                    {'AttributeName': hash_key, 'KeyType': 'HASH'},
                    {'AttributeName': 'version', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': hash_key, 'AttributeType': 'S'},
                    {'AttributeName': 'version', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )


def _flush_local_psql(create=True):
    with flask_wrapper.app.app_context():
        with supress(Exception):
            print('Dropping tables')
            db.drop_all()

        if create:
            print('Creating tables')
            db.create_all()


def _create_cognito_user_pool():
    '''
        Creates a cognito user pool and sets the id in the config manager
    '''
    cognito = get_client('cognito-idp')
    user_pool = cognito.create_user_pool(PoolName='test')
    pool_id = user_pool['UserPool']['Id']

    ConfigManager().set(
        ConfigManager._DEFAULT_TENANT_ID,
        key='user_pool_id',
        value=pool_id
    )


@pytest.fixture
def flush_local_dynamodb():
    yield

    _flush_local_dynamodb()
    _flush_local_psql()
    _create_cognito_user_pool()
    redis = InstanceManager().get_instance('', INSTANCE_TYPES.REDIS)
    redis.flushall()


def pytest_sessionstart(session):
    print('========= Initializing local dynamodb =========')
    _flush_local_dynamodb()
    _flush_local_psql()
    _create_cognito_user_pool()
    redis = InstanceManager().get_instance('', INSTANCE_TYPES.REDIS)
    redis.flushall()
    print('========= Finished initializing local dynamodb =========')


def pytest_sessionfinish(session, exitstatus):
    print()
    print('========= Cleaning up local dynamodb =========')
    _flush_local_dynamodb(create=False)
    # _flush_local_psql(create=False)
    redis = InstanceManager().get_instance('', INSTANCE_TYPES.REDIS)
    redis.flushall()
    print('========= Finished cleaning up local dynamodb =========')


def create_root():
    auth = AuthInfo(user_id='root', tenant_id='root')
    tenant = Tenant(name='root')
    tenant.save(auth)

    user = User(
        entity_id='root@root.com',
        name='root',
        family_name='',
        email='root@root.com',
        claims_by_audience={
            'user-management': [
                '*:user-management:*:*:*'
            ]
        }
    )
    user.save(auth)
    print("Created root tenant and user. {}".format({
        'tenant': tenant.entity_id,
        'user': user.entity_id
    }))


def main():
    _flush_local_dynamodb()
    _flush_local_psql()
    _create_cognito_user_pool()
    create_root()


if __name__ == "__main__":
    main()
