from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

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
    compliance_id = mf.Integer(requird=True, allow_null=False)
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

    compliance_id = db.Column(
        db.Integer,
        db.ForeignKey('compliances.id'),
        nullable=False,
    )
    date = db.Column(db.Date, nullable=False)
    pending = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Integer, nullable=False)
    failed = db.Column(db.Integer, nullable=False)
    remediation = db.Column(db.Integer, nullable=False)
    overdue = db.Column(db.Integer, nullable=False)

    compliance = db.relationship('Compliance')


@dataclass
class ComplianceTimelineListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceTimeline
