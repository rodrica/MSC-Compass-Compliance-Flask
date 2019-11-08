import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
    BaseOffsetListQueryParams, BaseOffsetListQueryParamsSchema,
)
from techlock.common.orm.sqlalchemy import (
    BaseModel, BaseModelSchema,
)

__all__ = [
    'Tenant',
    'TenantSchema',
    'TenantPageableSchema',
    'TenantListQueryParameters',
    'TenantListQueryParametersSchema',
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


class TenantSchema(BaseModelSchema):
    pass


class TenantPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(TenantSchema, many=True, dump_only=True)


class TenantListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    @ma.post_load
    def make_object(self, data, **kwargs):
        return TenantListQueryParameters(**data)


class Tenant(BaseModel):
    __tablename__ = 'tenants'


@dataclass
class TenantListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Tenant
