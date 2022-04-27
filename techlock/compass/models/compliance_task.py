import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from ..models.int_enum import IntEnum

__all__ = [
    'ComplianceTask',
    'ComplianceTaskSchema',
    'ComplianceTaskPageableSchema',
    'ComplianceTaskListQueryParameters',
    'ComplianceTaskListQueryParametersSchema',
    'COMPLIANCE_TASK_CLAIM_SPEC',
]


COMPLIANCE_TASK_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliance_tasks',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class Frequency(enum.Enum):
    weekly = 0
    monthly = 1
    quarterly = 2
    semiannually = 3
    annually = 4


class ComplianceTaskSchema(BaseModelSchema):
    frequency = EnumField(Frequency, required=True, allow_none=False)
    text = mf.String(required=True, allow_none=False)


class ComplianceTaskPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceTaskSchema, many=True, dump_only=True)


class ComplianceTaskListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliance_tasks by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceTaskListQueryParameters(**data)


class ComplianceTask(BaseModel):
    __tablename__ = 'compliance_tasks'

    frequency = sa.Column(IntEnum(Frequency), nullable=False)
    text = sa.Column(st.Text, nullable=False)


@dataclass
class ComplianceTaskListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceTask
