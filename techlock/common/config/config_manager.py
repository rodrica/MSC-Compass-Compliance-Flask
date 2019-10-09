import base64
import boto3
import dpath.util
import logging
import os
import requests
import yaml

from typing import Union, List

from techlock.common.singleton import Singleton
from techlock.common.caches import DefaultTTLCache
from techlock.common.util.serializers import deserialize_dynamo_obj, serialize_dynamo_obj

from .auth_info import AuthInfo

logger = logging.getLogger("config_manager")


def dpath_get(obj, glob, default=None, separator='.'):
    '''
        Simple wrapper for dpath.util.get that defaults `separator`='.'
        and returns `default` if glob is not found instead of raising a KeyError
    '''
    try:
        return dpath.util.get(obj, glob, separator)
    except Exception:
        return default


def dpath_set(obj, glob, value, separator='.'):
    dpath.util.set(obj, glob, value)


class ConfigManager(metaclass=Singleton):
    '''
        Responsible for loading configuration.
        Provides handy methods for getting certain config objects such as RedshiftConfig.

        Priority:
        1) static_config: If the key exists in the static_config, return it's value
        2) OS environment: If the key exsits in the OS env, return it's value. Note that dots (`.`) will be replaced with underscores (`_`)
        3) DynamoDB: Get value from DynamoDB.
        4) DynamoDB: Same as above but with '_default_' as tenant_id

        DynamoDB object will be cached for up to 1min by default. This means there is up to 60s delay after a change was made to the table.
    '''

    _DEFAULT_TENANT_ID = '_default_'
    _DEFAULT_STAGE = 'dev'

    def __init__(self, stage: str = None, cache_max_size: int = 64, cache_ttl: int = 60, table_tmpl: str = None, dynamo_endpoint_url=None):
        self.stage = stage or os.environ.get('STAGE', self._DEFAULT_STAGE)
        self.table_name = self._get_table_name(stage=self.stage)

        self.static_config = dict()
        self.config = DefaultTTLCache(self._get_config, max_size=cache_max_size, ttl=cache_ttl)
        self.dynamo_endpoint_url = dynamo_endpoint_url

    def _get_table_name(self, stage):
        separator = os.environ.get('DDB_SEPARATOR', '-')

        prefix = ''
        db_prefix = os.environ.get('DDB_PREFIX')
        if db_prefix:
            prefix = '{prefix}{sep}'.format(prefix=db_prefix, sep=separator)

        table_name = '{prefix}{stage}{sep}{table}'.format(
            prefix=prefix,
            stage=stage,
            sep=separator,
            table='config'
        ).upper()

        logger.debug('Using table: %s', table_name)
        return table_name

    def _get_region_name(self, session):
        region_name = session.region_name
        if not region_name:
            try:
                response = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=3)
                region_name = response.json().get('region')
            except Exception as e:
                logger.debug('Could not get EC2 instance-identity document, defaulting to "us-east-1". Error: %s', e)
                region_name = 'us-east-1'
        return region_name

    def _get_dynamodb_client(self):
        session = boto3.session.Session()
        region_name = self._get_region_name(session)
        dynamo_endpoint_url = self.dynamo_endpoint_url or os.environ.get('DYNAMODB_ENDPOINT_URL')
        dynamodb = session.client('dynamodb', region_name=region_name, endpoint_url=dynamo_endpoint_url)

        return dynamodb

    def _get_kms_client(self):
        session = boto3.session.Session()
        region_name = self._get_region_name(session)
        kms = session.client('kms', region_name=region_name)
        return kms

    def load_from_file(self, file) -> None:
        '''
            Load static_config from json or yaml file.
        '''
        with open(file, 'r') as f:
            config = yaml.loads(f.read(f))

            self.static_config.update(config)

    def _get_config(self, tenant_id: str) -> dict:
        '''
            Gets document from DynamoDB and parses it to native python dict.
        '''
        try:
            dynamodb = self._get_dynamodb_client()
            response = dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'tenant_id': {'S': tenant_id},
                    'version': {'S': '00000000000000000000000000000000'}
                }
            )
        except Exception:
            if self.stage == 'prod':
                raise
            else:
                return None

        if 'Item' in response:
            return deserialize_dynamo_obj(response['Item'])
        else:
            return None

    def get(self, current_user: AuthInfo, key: Union[str, List[str]], default=None, raise_if_not_found=False):
        '''
            Gets a single value from the config.
            Priority:
            1) static_config: If the key exists in the static_config, return it's value
            2) OS environment: If the key exsits in the OS env, return it's value. Note that dots (`.`) will be replaced with underscores (`_`)
            3) DynamoDB: Get value from DynamoDB.
            4) DynamoDB: Same as above but with '_default_' as tenant_id
        '''
        if isinstance(current_user, AuthInfo):
            tenant_id = current_user.tenant_id
        else:
            # legacy behavior
            tenant_id = current_user

        if isinstance(key, list):
            key = '.'.join(key)

        # 1.
        value = dpath_get(self.static_config, key)

        # 2.
        if value is None:
            os_key = key.replace('.', '_')
            value = os.environ.get(os_key, os.environ.get(os_key.upper()))

        # 3.
        if value is None:
            if tenant_id:
                client_config = self.config[tenant_id]
                if client_config:
                    value = dpath_get(client_config, key)
            default_config = self.config[self._DEFAULT_TENANT_ID]
            if value is None:
                value = dpath_get(default_config, key, default=default)

        if isinstance(value, str):
            if value.startswith('KMS: '):
                kms = self._get_kms_client()
                cipher = base64.b64decode(value[5:])
                value = kms.decrypt(CiphertextBlob=cipher)['Plaintext'].decode('utf8')

        if value is None and raise_if_not_found:
            raise Exception("Could not find configuration key: %s for client: %s" % (key, tenant_id))

        return value

    def set(self, current_user: AuthInfo, key: Union[str, List[str]], value):
        '''
            Sets a key=value.
            If key has '.' in it, we expect all parents to be maps.
        '''
        if isinstance(current_user, AuthInfo):
            tenant_id = current_user.tenant_id
        else:
            # legacy behavior
            tenant_id = current_user

        if isinstance(key, list):
            key = '.'.join(key)

        dynamodb = self._get_dynamodb_client()
        parts = key.split('.')
        # If the key is nested, we must first figure out if it exists, all parents must exists for update.
        client_config = self.config[tenant_id]
        if client_config:
            # See if the key or part of the key exist yet.
            last_removed_part = None
            found_value = dpath_get(client_config, key)
            while found_value is None and parts:
                last_removed_part = parts[-1]
                parts = parts[:-1]
                found_value = dpath_get(client_config, '.'.join(parts))
            if last_removed_part:
                if isinstance(found_value, dict):
                    parts.append(last_removed_part)  # reattach last not found part. This ensures we set the new dict key instead of overwrite the entire dict.
                else:
                    logger.warn(
                        'Overriding a non dict value with a dict. Key=%s, Value=%s, Found Key=%s, Found Value=%s',
                        key, value, '.'.join(parts), found_value
                    )

        map_keys = key.split('.')[len(parts):]
        ue_key = '.'.join(['#{}'.format(p) for p in parts])
        names = {'#{}'.format(p): p for p in parts}
        update_value = value
        for x in reversed(map_keys):
            update_value = {x: update_value}

        update_data = {
            'TableName': self.table_name,
            'Key': {
                'tenant_id': {'S': tenant_id},
                'version': {'S': '00000000000000000000000000000000'}
            },
            'UpdateExpression': 'SET {} = :value'.format(ue_key),
            'ExpressionAttributeNames': names,
            'ExpressionAttributeValues': serialize_dynamo_obj({':value': update_value})
        }
        print("Updating: %s", update_data)
        logger.debug("Updating: %s", update_data)
        dynamodb.update_item(**update_data)
        # Clear cache so that we get the updated value on next call.
        del self.config[tenant_id]
