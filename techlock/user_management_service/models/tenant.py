import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass
from sqlalchemy import func as sa_fn
from sqlalchemy.dialects.postgresql import JSONB

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
    OffsetPageableQueryParameters, OffsetPageableQueryParametersSchema,
)
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import (
    db,
    BaseModel, BaseModelSchema,
    get_string_filter,
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
    name = mf.String()
    description = mf.String(allow_none=True)

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class TenantPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(TenantSchema, many=True, dump_only=True)


class TenantListQueryParametersSchema(OffsetPageableQueryParametersSchema):
    name = mf.String(allow_none=True, description='Used to filter tenants by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return TenantListQueryParameters(**data)


class Tenant(BaseModel):
    __tablename__ = 'tenants'

    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)

    tags = db.Column(JSONB, nullable=True)


@dataclass
class TenantListQueryParameters(OffsetPageableQueryParameters):
    name: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = list()

        if self.name is not None:
            filters.append(get_string_filter(sa_fn.lower(Tenant.name), self.name))

        return filters
