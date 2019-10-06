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
    'Tenant',
    'TenantSchema',
    'TenantPageableSchema',
    'TENANT_CLAIM_SPEC',
]


TENANT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='tenants',
    filter_fields=[]
)


class TenantSchema(PersistedObjectSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class TenantPageableSchema(PageableResponseBaseSchema):
    items = mf.Nested(TenantSchema, many=True, dump_only=True)


@dataclass
class Tenant(PersistedObject):
    table: ClassVar[str] = 'tenants'

    name: str = NO_DEFAULT
    description: str = None

    tags: Dict[str, str] = None
