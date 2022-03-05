import os
import enum
from dataclasses import dataclass
from humanfriendly.terminal import enable_ansi_support

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from pkg_resources import require

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool
from sqlalchemy.sql.elements import True_
from sqlalchemy.sql.operators import nulls_last_op

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db
from techlock.compas.models.audit import Audit, AuditSchema

from techlock.compas.models.report import ReportSchema
from techlock.compas.routes import audits

from ..models.int_enum import IntEnum

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
STAGE = os.environ.get('STAGE', 'dev').upper()


class AuditTimelineSchema(BaseModelSchema):
    audit_id = mf.Integer()
    date = mf.Date(required=True, allow_none=False)
    compliant = mf.Integer(requird=True, allow_none=False)
    notice = mf.Integer(requird=True, allow_none=False)
    noncompliant = mf.Integer(requird=True, allow_none=False)
    pending = mf.Integer(requird=True, allow_none=False)

    audit = mf.Nested(AuditSchema, dump_only=True)


class AuditTimelinePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditTimelineSchema, many=True, dump_only=True)


class AuditTimelineListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter audits_timeline by name prefix.')

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

