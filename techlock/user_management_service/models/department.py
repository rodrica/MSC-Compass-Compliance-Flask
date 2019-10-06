import marshmallow.fields as mf
from dataclasses import dataclass
from typing import ClassVar, Dict

from techlock.common.api import ClaimSpec, PageableResponseBaseSchema
from techlock.common.orm.dynamodb import (
    NO_DEFAULT,
    PersistedObject,
    PersistedObjectSchema,
)

__all__ = [
    'Department',
    'DepartmentSchema',
    'DepartmentPageableSchema',
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


@dataclass
class Department(PersistedObject):
    table: ClassVar[str] = 'departments'

    name: str = NO_DEFAULT
    description: str = None

    tags: Dict[str, str] = None
