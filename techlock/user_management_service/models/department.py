from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

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
    filter_fields=[
        'name',
        'created_by',
    ]
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
