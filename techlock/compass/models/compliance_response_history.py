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

from techlock.compass.models.compliance_response import Phase, Status

__all__ = [
    'ComplianceResponseHistory',
    'ComplianceResponseHistorySchema',
    'ComplianceResponseHistoryPageableSchema',
    'ComplianceResponseHistoryListQueryParameters',
    'ComplianceResponseHistoryListQueryParametersSchema',
    'COMPLIANCE_RESPONSE_HISTORY_CLAIM_SPEC',
]


COMPLIANCE_RESPONSE_HISTORY_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read',
    ],
    resource_name='compliance_responses_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class ComplianceResponseHistorySchema(BaseModelSchema):
    compliance_response_id = mf.String(dump_only=True)
    compliance_id = mf.String(requird=True, allow_null=False)
    period_id = mf.String(requird=True, allow_null=False)
    phase = EnumField(Phase, requird=True, allow_null=False)
    status = EnumField(Status, requird=True, allow_null=False)


class ComplianceResponseHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(
        ComplianceResponseHistorySchema,
        many=True,
        dump_only=True,
    )


class ComplianceResponseHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliance_responses_history by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceResponseHistoryListQueryParameters(**data)


class ComplianceResponseHistory(BaseModel):
    __tablename__ = 'compliance_responses_history'

    compliance_response_id = sa.Column(UUID, sa.ForeignKey('compliance_responses.id'), nullable=False)
    compliance_id = sa.Column(UUID, sa.ForeignKey('compliances.id'), nullable=False)
    period_id = sa.Column(UUID, sa.ForeignKey('compliance_periods.id'), nullable=False)
    phase = sa.Column(st.Enum(Phase), nullable=False)
    status = sa.Column(st.Enum(Status), nullable=False)


@dataclass
class ComplianceResponseHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceResponseHistory
