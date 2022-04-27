import os

import boto3
import pytest
from techlock.common.api.flask import create_flask
from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.orm.sqlalchemy import db
from techlock.common.util.helper import supress

flask_wrapper = create_flask(__name__, enable_jwt=False, audience='rules-service')


def _flush_local_dynamodb(create=True):
    if os.name == 'nt':
        raise Exception("Can't run on Windows. Bug in `time` module causes `dynamodb.create_table` to fail.")

    print('endpoint_url: %s' % os.environ['DYNAMODB_ENDPOINT_URL'])
    ddb = boto3.client('dynamodb', endpoint_url=os.environ['DYNAMODB_ENDPOINT_URL'])
    tables = [
        ConfigManager().table_name,
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
                    {'AttributeName': 'version', 'KeyType': 'RANGE'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': hash_key, 'AttributeType': 'S'},
                    {'AttributeName': 'version', 'AttributeType': 'S'},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10,
                },
            )


def _flush_local_psql(create=True):
    with flask_wrapper.app.app_context():
        with supress(Exception):
            print('Dropping tables')
            db.drop_all()

        if create:
            print('Creating tables')
            db.create_all()


@pytest.fixture
def flush_local_dynamodb():
    yield

    _flush_local_dynamodb()
    _flush_local_psql()


def pytest_sessionstart(session):
    print('========= Initializing local dynamodb =========')
    _flush_local_dynamodb()
    _flush_local_psql()
    print('========= Finished initializing local dynamodb =========')


def pytest_sessionfinish(session, exitstatus):
    print()
    print('========= Cleaning up local dynamodb =========')
    _flush_local_dynamodb(create=False)
    print('========= Finished cleaning up local dynamodb =========')



def main():
    _flush_local_dynamodb()
    _flush_local_psql()


if __name__ == "__main__":
    main()
