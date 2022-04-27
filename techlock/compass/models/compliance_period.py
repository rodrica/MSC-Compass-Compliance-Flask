from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

__all__ = [
    'CompliancePeriod',
    'CompliancePeriodSchema',
    'CompliancePeriodPageableSchema',
    'CompliancePeriodListQueryParameters',
    'CompliancePeriodListQueryParametersSchema',
    'COMPLIANCE_PERIOD_CLAIM_SPEC',
]


COMPLIANCE_PERIOD_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliance_periods',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class CompliancePeriodSchema(BaseModelSchema):
    compliance_id = mf.String(require=True, allow_none=False)
    task_id = mf.String(require=True, allow_none=False)
    start_date = mf.Date(require=True, allow_none=False)
    end_date = mf.Date(required=True, allow_none=False)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    task = mf.Nested('ComplianceTaskSchema', dump_only=True)


class CompliancePeriodPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(CompliancePeriodSchema, many=True, dump_only=True)


class CompliancePeriodListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliance_periods by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return CompliancePeriodListQueryParameters(**data)


class CompliancePeriod(BaseModel):
    __tablename__ = 'compliance_periods'

    compliance_id = sa.Column(UUID, sa.ForeignKey('compliances.id'), nullable=False)
    task_id = sa.Column(UUID, sa.ForeignKey('compliance_tasks.id'), nullable=False)
    start_date = sa.Column(st.Date, nullable=False)
    end_date = sa.Column(st.Date, nullable=False)

    compliance = relationship('Compliance')
    task = relationship('ComplianceTask')


@dataclass
class CompliancePeriodListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = CompliancePeriod
