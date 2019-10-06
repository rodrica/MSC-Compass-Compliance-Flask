import json
from boto3.dynamodb import types as dynamodb_types
from dataclasses import is_dataclass, asdict
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from typing import Dict


__all__ = [
    'deserialize_dynamo_obj',
    'serialize_dynamo_obj',
    'JSONEncoder',
    'JSONSerializer',
    'JSONDeserializer',
]


def deserialize_dynamo_obj(obj: dict) -> dict:
    deserializer = dynamodb_types.TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in obj.items()}


def serialize_dynamo_obj(obj: dict) -> dict:
    serializer = dynamodb_types.TypeSerializer()

    def serialize(v):
        if v == '':
            return serializer.serialize(None)
        elif isinstance(v, float):
            return serializer.serialize(Decimal(str(v)))
        else:
            return serializer.serialize(v)
    return {k: serialize(v) for k, v in obj.items()}


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif is_dataclass(obj):
            return asdict(obj)
        return json.JSONEncoder.default(self, obj)


class JSONSerializer(JSONEncoder):
    '''
        Serializes dataclasses in such away that we can deserialize back.
    '''
    def default(self, obj):
        if is_dataclass(obj):
            return {
                'dataclass': obj.__class__.__name__,
                'module': obj.__class__.__module__,
                'data': asdict(obj)
            }
        elif isinstance(obj, datetime):
            return {
                'class': 'datetime',
                'format': 'iso8601',
                'data': obj.isoformat()
            }
        return JSONEncoder.default(self, obj)


class JSONDeserializer(json.JSONDecoder):
    '''
        Deserializes Json strings with dataclasses as output by JSONSerializer
    '''
    def __init__(
        self, *args, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, strict=True,
        object_pairs_hook=None
    ):
        super(JSONDeserializer, self).__init__(
            *args,
            object_hook=object_hook if object_hook is not None else self.deserialize_object,
            parse_float=parse_float,
            parse_int=parse_int, parse_constant=parse_constant, strict=strict,
            object_pairs_hook=object_pairs_hook
        )

    def deserialize_object(self, obj: Dict):
        if 'dataclass' in obj and 'module' in obj:
            module = import_module(obj['module'])
            d_class = getattr(module, obj['dataclass'])
            return d_class(**obj['data'])
        elif 'class' in obj:
            if obj['class'] == 'datetime':
                return self.deserialize_datetime(self, obj)
        return obj

    def deserialize_datetime(self, obj: Dict):
        if 'format' in obj:
            if obj['format'] == 'isoformat':
                return datetime.fromisoformat(obj['data'])
        return obj
