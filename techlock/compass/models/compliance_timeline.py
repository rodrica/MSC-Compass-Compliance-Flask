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
    'ComplianceTimeline',
    'ComplianceTimelineSchema',
    'ComplianceTimelinePageableSchema',
    'ComplianceTimelineListQueryParameters',
    'ComplianceTimelineListQueryParametersSchema',
    'COMPLIANCE_TIMELINE_CLAIM_SPEC',
]


COMPLIANCE_TIMELINE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliances_timeline',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class ComplianceTimelineSchema(BaseModelSchema):
    compliance_id = mf.String(requird=True, allow_null=False)
    date = mf.Date(requird=True, allow_null=False)
    pending = mf.Integer(requird=True, allow_null=False)
    passed = mf.Integer(requird=True, allow_null=False)
    failed = mf.Integer(requird=True, allow_null=False)
    remediation = mf.Integer(requird=True, allow_null=False)
    overdue = mf.Integer(requird=True, allow_null=False)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)


class ComplianceTimelinePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceTimelineSchema, many=True, dump_only=True)


class ComplianceTimelineListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliances_timeline by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceTimelineListQueryParameters(**data)


class ComplianceTimeline(BaseModel):
    __tablename__ = 'compliances_timeline'

    compliance_id = sa.Column(UUID, sa.ForeignKey('compliances.id'), nullable=False)
    date = sa.Column(st.Date, nullable=False)
    pending = sa.Column(st.Integer, nullable=False)
    passed = sa.Column(st.Integer, nullable=False)
    failed = sa.Column(st.Integer, nullable=False)
    remediation = sa.Column(st.Integer, nullable=False)
    overdue = sa.Column(st.Integer, nullable=False)

    compliance = relationship('Compliance')


@dataclass
class ComplianceTimelineListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceTimeline
