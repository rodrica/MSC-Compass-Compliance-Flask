from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

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
    service_now_id = mf.String(allow_none=True)


class TenantPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(TenantSchema, many=True, dump_only=True)


class TenantListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    @ma.post_load
    def make_object(self, data, **kwargs):
        return TenantListQueryParameters(**data)


class Tenant(BaseModel):
    __tablename__ = 'tenants'

    service_now_id = db.Column(db.String, nullable=True)


@dataclass
class TenantListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Tenant
