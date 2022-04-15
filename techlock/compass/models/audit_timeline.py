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
    'AuditTimeline',
    'AuditTimelineSchema',
    'AuditTimelinePageableSchema',
    'AuditTimelineListQueryParameters',
    'AuditTimelineListQueryParametersSchema',
    'AUDIT_TIMELINE_CLAIM_SPEC',
]


AUDIT_TIMELINE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='audits_timeline',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class AuditTimelineSchema(BaseModelSchema):
    audit_id = mf.Integer()
    date = mf.Date(required=True, allow_none=False)
    compliant = mf.Integer(requird=True, allow_none=False)
    notice = mf.Integer(requird=True, allow_none=False)
    noncompliant = mf.Integer(requird=True, allow_none=False)
    pending = mf.Integer(requird=True, allow_none=False)

    audit = mf.Nested('AuditSchema', dump_only=True)


class AuditTimelinePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditTimelineSchema, many=True, dump_only=True)


class AuditTimelineListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter audits_timeline by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditTimelineListQueryParameters(**data)


class AuditTimeline(BaseModel):
    __tablename__ = 'audits_timeline'

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"))
    date = db.Column(db.Date, nullable=True)
    compliant = db.Column(db.Integer, nullable=False)
    notice = db.Column(db.Integer, nullable=False)
    noncompliant = db.Column(db.Integer, nullable=False)
    pending = db.Column(db.Integer, nullable=False)

    audit = db.relationship('Audit')


@dataclass
class AuditTimelineListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditTimeline
