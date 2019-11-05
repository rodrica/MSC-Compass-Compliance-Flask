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


class RoleSchema(BaseModelSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String()),
        allow_none=True
    )

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class RolePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(RoleSchema, many=True, dump_only=True)


class RoleListQueryParametersSchema(OffsetPageableQueryParametersSchema):
    name = mf.String(allow_none=True, description='Used to filter roles by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return RoleListQueryParameters(**data)


class Role(BaseModel):
    __tablename__ = 'roles'

    name = db.Column(db.String, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=True)

    claims_by_audience = db.Column(JSONB, nullable=True)
    tags = db.Column(JSONB, nullable=True)


@dataclass
class RoleListQueryParameters(OffsetPageableQueryParameters):
    name: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = list()

        if self.name is not None:
            filters.append(get_string_filter(sa_fn.lower(Role.name), self.name))

        return filters
