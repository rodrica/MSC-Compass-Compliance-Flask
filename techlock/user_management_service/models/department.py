import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass
from sqlalchemy import func as sa_fn
from sqlalchemy.dialects.postgresql import JSONB

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
    OffsetPageableQueryParameters, OffsetPageableQueryParametersSchema,
    SortableQueryParameters, SortableQueryParametersSchema,
)
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import (
    db,
    BaseModel, BaseModelSchema,
    get_string_filter,
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


class DepartmentSchema(BaseModelSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class DepartmentPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(DepartmentSchema, many=True, dump_only=True)


class DepartmentListQueryParametersSchema(OffsetPageableQueryParametersSchema, SortableQueryParametersSchema):
    name = mf.String(allow_none=True, description='Used to filter departments by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return DepartmentListQueryParameters(**data)


class Department(BaseModel):
    __tablename__ = 'departments'

    name = db.Column(db.String, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=True)

    tags = db.Column(JSONB, nullable=True)


@dataclass
class DepartmentListQueryParameters(OffsetPageableQueryParameters, SortableQueryParameters):
    name: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = list()

        if self.name is not None:
            filters.append(get_string_filter(sa_fn.lower(Department.name), self.name))

        return filters
