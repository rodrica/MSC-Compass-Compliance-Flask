
import boto3
import json
import marshmallow as ma
import marshmallow.fields as mf
import logging
import os
from boto3.dynamodb.conditions import Attr, ConditionBase, ConditionExpressionBuilder
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from typing import _GenericAlias, ClassVar, Dict, List, Union
from uuid import uuid4

from ...api import (
    BadRequestException, PageableResponse, Claim,
    claims_to_dynamodb_condition,
    filter_by_claims,
)
from ...config import AuthInfo
from ...util.aws import get_client
from ...util.serializers import deserialize_dynamo_obj, serialize_dynamo_obj


logger = logging.getLogger('persisted_object')
NO_DEFAULT = object()


def get_ddb():
    if 'DYNAMODB_ENDPOINT_URL' in os.environ:
        ddb = boto3.client('dynamodb', endpoint_url=os.environ['DYNAMODB_ENDPOINT_URL'])
    else:
        ddb = get_client('dynamodb')
    return ddb


class PersistedObjectSchema(ma.Schema):
    class Meta:
        ordered = True

    entity_id = mf.String(dump_only=True)
    tenant_id = mf.String(dump_only=True)
    version = mf.String(dump_only=True)
    previous_version = mf.String(dump_only=True)
    is_latest = mf.Boolean(dump_only=True)
    is_active = mf.Boolean(dump_only=True)
    created_on = mf.String(dump_only=True)
    created_by = mf.String(dump_only=True)
    changed_on = mf.String(dump_only=True)
    changed_by = mf.String(dump_only=True)


@dataclass
class PersistedObject:
    '''
        Python Dataclass that is persisted on AWS DynamoDB
    '''
    table: ClassVar[str]
    is_entity_id_required: ClassVar[bool] = False

    entity_id: str = None
    version: str = None
    previous_version: str = None
    is_latest: bool = True
    is_active: bool = True
    tenant_id: str = None
    created_on: str = None
    created_by: str = None
    changed_on: str = None
    changed_by: str = None

    def __post_init__(self):
        for key, value in self.__dict__.items():
            if value is NO_DEFAULT:
                raise TypeError(
                    f"__init__ missing 1 required argument: '{key}'"
                )

    @classmethod
    def protected_fields(cls):
        fields = [
            'version',
            'previous_version',
            'is_latest',
            'is_active',
            'tenant_id',
            'created_on',
            'created_by',
            'changed_on',
            'changed_by'
        ]
        if not cls.is_entity_id_required:
            fields.append('entity_id')
        return fields

    @classmethod
    def custom_type_json_encoders(cls):
        return {
            'bytes': lambda x: x.hex(),
            'Decimal': float
        }

    @classmethod
    def custom_type_json_decoders(cls):
        return {
            'bytes': lambda x: bytes.fromhex(x),
            'Decimal': Decimal
        }

    @classmethod
    def custom_json_encoders(cls):
        return dict()

    @classmethod
    def custom_json_decoders(cls):
        return dict()

    @classmethod
    def validate(
        cls,
        obj: Dict,
        validate_required_fields: bool = True
    ):
        '''
            Validates the dictionary object.
            Args:
                obj (Dict): Dictionary to validate
                validate_required_fields (bool): Do we need to validate required fields, set to False when validating an update
        '''
        fields = dict(cls.__dataclass_fields__)
        # 1. Remove all automated fields. These are ignored when provided by the user
        for x in cls.protected_fields():
            fields.pop(x, None)
            obj.pop(x, None)

        # 2. Validate that required fields are defined
        if validate_required_fields:
            cls._validate_required_fields(obj, fields)

        # 3. Validate that there are no unknown fields defined
        unknown_fields = [x for x in obj if x not in fields]
        if unknown_fields:
            raise BadRequestException("Unknown fields provided: {}".format(unknown_fields))

        # 4. Validate that all types match
        cls._validate_types(obj, fields)

        return True

    @classmethod
    def _validate_required_fields(cls, obj, fields):
        required_fields = list()
        for k, v in fields.items():
            if (v.default == NO_DEFAULT or (cls.is_entity_id_required and k == 'entity_id')) and (k not in obj or obj[k] is None):
                required_fields.append(k)
        if required_fields:
            raise BadRequestException("Required fields were not defined: {}".format(required_fields))

    @classmethod
    def _validate_types(cls, obj, fields):
        invalid_types = dict()
        for k, v in obj.items():
            if v is None:
                continue

            expected_type = fields[k].type
            if isinstance(expected_type, _GenericAlias) and expected_type.__origin__ == list:
                invalid_type = cls._validate_list_type(v, expected_type)
                if invalid_type:
                    invalid_types[k] = invalid_type
            elif (isinstance(expected_type, _GenericAlias)):
                if not isinstance(v, expected_type.__origin__):
                    # lazy approach - should probably check for nested fields like we do for list
                    invalid_types[k] = "Provided: {}, Expected type: {}".format(v, expected_type.__origin__.__name__)
            elif expected_type == Decimal:
                try:
                    Decimal("{}".format(v))
                except Exception:
                    invalid_types[k] = "Provided: {}, Expected decimal as string".format(v)
            elif not isinstance(v, expected_type):
                invalid_types[k] = "Provided: {}, Expected type: {}".format(v, expected_type.__name__)

        if invalid_types:
            raise BadRequestException("Fields are of the wrong type: {}".format(invalid_types).replace('\"', "'"))

    @classmethod
    def _validate_list_type(cls, obj, expected_type):
        invalid_type = None
        if not isinstance(obj, list):
            invalid_type = "Provided: {}, Expected type: {}".format(obj, list)
        else:
            expected_type = expected_type.__args__[0]
            invalid_types_nested = list()
            for x in obj:
                if x is not None and not isinstance(x, expected_type):
                    invalid_types_nested.append("Invalid nested type. Provided: {}, Expected type: {}".format(obj, expected_type.__name__))
            if invalid_types_nested:
                invalid_type = invalid_types_nested

        return invalid_type

    @classmethod
    def _get_table_name(cls):
        prefix = ''
        db_prefix = os.environ.get('DB_PREFIX')
        if db_prefix:
            prefix = '{}.'.format(db_prefix)
        table_name = '{}{}.{}'.format(prefix, os.environ.get('STAGE'), cls.table)

        logger.debug('Using table: %s', table_name)
        return table_name

    def asdict(self):
        '''
            Return the instance as a dictionary
        '''
        return asdict(self)

    def asjson(self):
        '''
            Return the instance as a json string
        '''
        raw_dict = self.asdict()
        type_encoders = self.custom_type_json_encoders()
        field_encoders = self.custom_json_encoders()

        encoded_dict = dict()
        for key, value in raw_dict.items():
            if key in field_encoders:
                encoded_dict[key] = field_encoders[key](value)
            elif type(value).__name__ in type_encoders:
                encoded_dict[key] = type_encoders[type(value).__name__](value)
            else:
                encoded_dict[key] = value

        return json.dumps(encoded_dict)

    @classmethod
    def from_json(cls, json_str: str):
        '''
            Return the instance from the json string
        '''
        raw_dict = json.loads(json_str)
        decoded_dict = dict()

        type_decoders = cls.custom_type_json_decoders()
        field_decoders = cls.custom_json_decoders()

        for key, field in cls.__dataclass_fields__.items():
            if key not in raw_dict:
                continue

            if key in field_decoders:
                decoded_dict[key] = field_decoders[key](raw_dict[key])
            elif field.type.__name__ in type_decoders:
                decoded_dict[key] = type_decoders[field.type.__name__](raw_dict[key])
            else:
                decoded_dict[key] = raw_dict[key]

        return cls(**decoded_dict)

    def _save(self):
        '''
            Saves the object in dynamodb and set audit fields
        '''
        ddb = get_ddb()
        self.version = str(uuid4().hex)
        self.is_latest = True
        self.changed_on = datetime.now().isoformat()
        if not self.created_on:
            self.created_on = datetime.now().isoformat()

        if not self.entity_id:
            self.entity_id = str(uuid4().hex)

        resp = ddb.put_item(
            TableName=self._get_table_name(),
            Item=serialize_dynamo_obj(asdict(self))
        )
        return resp

    def save(self, auth_info: AuthInfo):
        '''
            Saves the instance (create or update)
        '''
        ddb = get_ddb()
        # version is defined, so we're updating
        if self.version:
            self.previous_version = self.version
            self.changed_by = auth_info.user_id
            # Put new item
            self._save()

            # Update old item only if putting the new item was successfull
            resp = ddb.update_item(
                TableName=self._get_table_name(),
                Key=serialize_dynamo_obj({
                    'entity_id': self.entity_id,
                    'version': self.previous_version
                }),
                UpdateExpression="set is_latest = :is_latest",
                ExpressionAttributeValues=serialize_dynamo_obj({
                    ':is_latest': False,
                })
            )
            return resp
        # no version so new object
        else:
            self.tenant_id = auth_info.tenant_id
            self.created_by = auth_info.user_id
            self.changed_by = auth_info.user_id
            return self._save()

    def delete(self, auth_info: AuthInfo):
        '''
            Soft-deletes the instance
        '''
        self.is_active = False
        return self.save(auth_info)

    def get_previous_versions(self, limit=1, start_version=None):
        ddb = get_ddb()
        items = list()

        version = start_version or self.previous_version
        for idx in range(limit):
            resp = ddb.get_item(
                TableName=self._get_table_name(),
                Key=serialize_dynamo_obj({
                    'entity_id': self.entity_id,
                    'version': version
                })
            )
            office = self.__class__(**deserialize_dynamo_obj(resp['Item']))
            items.append(office)
            version = office.previous_version
            if not version:
                break

        response = PageableResponse(
            items=items,
            last_key=version
        )
        return response

    @classmethod
    def get(cls, auth_info: AuthInfo, entity_id):
        ddb = get_ddb()
        # TODO: Handle empty table
        resp = ddb.query(
            TableName=cls._get_table_name(),
            KeyConditionExpression='entity_id = :entity_id',
            FilterExpression='is_latest = :is_latest AND is_active = :is_active AND tenant_id = :tenant_id',
            ExpressionAttributeValues=serialize_dynamo_obj({
                ':entity_id': entity_id,
                ':is_latest': True,
                ':is_active': True,
                ':tenant_id': auth_info.tenant_id
            })
        )

        if 'Items' in resp and resp['Items']:
            items = resp['Items']
            if len(items) > 1:
                logger.warn('Multiple items returned for entity_id: %s, %s', entity_id, len(items))

            return cls(**deserialize_dynamo_obj(items[0]))
        else:
            return

    @classmethod
    def _unsecure_get(cls, entity_id):
        '''
            Only use this if you are absolutely sure.
            This gets the entity without tenant isolation.
            There are only a handful of usecases for this.
        '''
        ddb = get_ddb()
        # TODO: Handle empty table
        resp = ddb.query(
            TableName=cls._get_table_name(),
            KeyConditionExpression='entity_id = :entity_id',
            FilterExpression='is_latest = :is_latest AND is_active = :is_active',
            ExpressionAttributeValues=serialize_dynamo_obj({
                ':entity_id': entity_id,
                ':is_latest': True,
                ':is_active': True,
            })
        )

        if 'Items' in resp and resp['Items']:
            items = resp['Items']
            if len(items) > 1:
                logger.warn('Multiple items returned for entity_id: %s, %s', entity_id, len(items))

            return cls(**deserialize_dynamo_obj(items[0]))
        else:
            return None

    @classmethod
    def get_all(
        cls,
        auth_info: AuthInfo,
        ids: List[str] = None,
        limit: int = 100,
        start_key: str = None,
        created_by_user_id: str = None,
        additional_conditions: Union[ConditionBase, List[ConditionBase]] = None,
        claims: List[Claim] = None,
    ) -> PageableResponse:
        if claims is None:
            return PageableResponse(items=[])

        ddb = get_ddb()
        items = list()
        expression = Attr('is_latest').eq(True) \
            & Attr('is_active').eq(True) \
            & Attr('tenant_id').eq(auth_info.tenant_id)
        request_dict = {
            'TableName': cls._get_table_name(),
            'Limit': limit
        }
        if ids:
            expression &= Attr('entity_id').is_in(ids)
        if created_by_user_id:
            expression &= Attr('created_by').eq(created_by_user_id)
        if additional_conditions:
            if isinstance(additional_conditions, list):
                for condition in additional_conditions:
                    expression &= condition
            else:
                expression &= additional_conditions
        claim_condition = claims_to_dynamodb_condition(claims)
        if claim_condition:
            expression &= claim_condition

        expr = ConditionExpressionBuilder().build_expression(expression)
        request_dict['FilterExpression'] = expr.condition_expression
        request_dict['ExpressionAttributeNames'] = expr.attribute_name_placeholders
        request_dict['ExpressionAttributeValues'] = serialize_dynamo_obj(expr.attribute_value_placeholders)

        while len(items) < limit:
            if start_key:
                if isinstance(start_key, str):
                    start_key = json.loads(start_key)
                request_dict['ExclusiveStartKey'] = start_key
            else:
                request_dict.pop('ExclusiveStartKey', None)

            resp = ddb.scan(**request_dict)
            resp_items = [cls(**deserialize_dynamo_obj(item)) for item in resp['Items']]
            if claims:
                resp_items = filter_by_claims(resp_items, claims)

            items.extend(resp_items)
            if 'LastEvaluatedKey' in resp and resp['LastEvaluatedKey']:
                start_key = json.dumps(resp['LastEvaluatedKey'])
            else:
                start_key = None
                break

        response = PageableResponse(
            items=items,
            last_key=start_key
        )
        return response
