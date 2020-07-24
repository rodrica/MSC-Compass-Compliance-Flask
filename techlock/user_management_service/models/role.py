import marshmallow as ma
import marshmallow.fields as mf
import os
from dataclasses import dataclass
from sqlalchemy.dialects.postgresql import JSONB

from techlock.common.api import (
    Claim, ClaimSpec,
    OffsetPageableResponseBaseSchema,
    BaseOffsetListQueryParams, BaseOffsetListQueryParamsSchema,
)
from techlock.common.orm.sqlalchemy import (
    db,
    BaseModel, BaseModelSchema,
)

__all__ = [
    'Role',
    'RoleSchema',
    'RolePageableSchema',
    'RoleListQueryParameters',
    'RoleListQueryParametersSchema',
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
STAGE = os.environ.get('STAGE', 'dev').upper()


class RoleSchema(BaseModelSchema):
    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String(validate=Claim.validate_claim_string)),
        allow_none=True
    )


class RolePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(RoleSchema, many=True, dump_only=True)


class RoleListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter roles by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return RoleListQueryParameters(**data)


class Role(BaseModel):
    __tablename__ = 'roles'

    claims_by_audience = db.Column(JSONB, nullable=True)

    @property
    def idp_name(self):
        return f'{self.tenant_id}_{STAGE}_{self.name}'


@dataclass
class RoleListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Role
