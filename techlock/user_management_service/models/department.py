import marshmallow as ma
import marshmallow.fields as mf
from boto3.dynamodb.conditions import Attr
from dataclasses import dataclass
from typing import ClassVar, Dict

from techlock.common.api import (
    ClaimSpec,
    PageableResponseBaseSchema,
    PageableQueryParameters, PageableQueryParametersSchema,
)
from techlock.common.orm.dynamodb import (
    NO_DEFAULT,
    PersistedObject,
    PersistedObjectSchema,
)

__all__ = [
    'Department',
    'DepartmentSchema',
    'DepartmentPageableSchema',
    'DepartmentListQueryParameters',
    'DepartmentListQueryParametersSchema',
    'DEPARTMENT_CLAIM_SPEC',
]


DEPARTMENT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='departments',
    filter_fields=[]
)


class DepartmentSchema(PersistedObjectSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class DepartmentPageableSchema(PageableResponseBaseSchema):
    items = mf.Nested(DepartmentSchema, many=True, dump_only=True)


class DepartmentListQueryParametersSchema(PageableQueryParametersSchema):
    name = mf.String(allow_none=True, description='Used to filter departments by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return DepartmentListQueryParameters(**data)


@dataclass
class Department(PersistedObject):
    table: ClassVar[str] = 'departments'

    name: str = NO_DEFAULT
    description: str = None

    tags: Dict[str, str] = None


@dataclass
class DepartmentListQueryParameters(PageableQueryParameters):
    name: str = None

    def get_filters(self):
        ddb_attrs = list()

        if self.name is not None:
            ddb_attrs.append(Attr('name').begins_with(self.name))

        return ddb_attrs
