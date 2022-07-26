import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import UUID
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

__all__ = [
    'ComplianceResponse',
    'ComplianceResponseSchema',
    'ComplianceResponsePageableSchema',
    'ComplianceResponseListQueryParameters',
    'ComplianceResponseListQueryParametersSchema',
    'COMPLIANCE_RESPONSE_CLAIM_SPEC',
]


COMPLIANCE_RESPONSE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliance_responses',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class Phase(enum.Enum):
    gathering = 0
    review = 1
    verification = 2
    finalized = 3


class Status(enum.Enum):
    pending = 0
    passed = 1
    failed = 2
    remediation = 3


class ComplianceResponseSchema(BaseModelSchema):
    compliance_id = mf.String(requird=True, allow_null=False)
    period_id = mf.String(requird=True, allow_null=False)
    phase = EnumField(Phase, requird=True, allow_null=False)
    status = EnumField(Status, requird=True, allow_null=False)


class ComplianceResponsePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceResponseSchema, many=True, dump_only=True)


class ComplianceResponseListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliance_responses by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceResponseListQueryParameters(**data)


class ComplianceResponse(BaseModel):
    __tablename__ = 'compliance_responses'

    compliance_id = sa.Column(UUID, sa.ForeignKey('compliances.id'), nullable=False)
    period_id = sa.Column(UUID, sa.ForeignKey('compliance_periods.id'), nullable=False)
    phase = sa.Column(st.Enum(Phase), nullable=False)
    status = sa.Column(st.Enum(Status), nullable=False)


@dataclass
class ComplianceResponseListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceResponse
