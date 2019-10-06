import marshmallow.fields as mf
from dataclasses import dataclass
from typing import ClassVar, Dict, List

from techlock.common.api import ClaimSpec, PageableResponseBaseSchema
from techlock.common.orm.dynamodb import (
    NO_DEFAULT,
    PersistedObject,
    PersistedObjectSchema,
)

__all__ = [
    'Role',
    'RoleSchema',
    'RolePageableSchema',
    'ROLE_CLAIM_SPEC',
]


ROLE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='roles',
    filter_fields=[]
)


class RoleSchema(PersistedObjectSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String()),
        allow_none=True
    )

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class RolePageableSchema(PageableResponseBaseSchema):
    items = mf.Nested(RoleSchema, many=True, dump_only=True)


@dataclass
class Role(PersistedObject):
    table: ClassVar[str] = 'roles'

    name: str = NO_DEFAULT
    description: str = None

    claims_by_audience: Dict[str, List[str]] = None

    tags: Dict[str, str] = None
