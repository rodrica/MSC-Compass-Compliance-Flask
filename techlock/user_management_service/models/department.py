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
    pass


class DepartmentPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(DepartmentSchema, many=True, dump_only=True)


class DepartmentListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    @ma.post_load
    def make_object(self, data, **kwargs):
        return DepartmentListQueryParameters(**data)


class Department(BaseModel):
    __tablename__ = 'departments'


@dataclass
class DepartmentListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Department
