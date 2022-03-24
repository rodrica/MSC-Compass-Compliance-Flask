from json import dump
import os
import enum
from dataclasses import dataclass
from humanfriendly.terminal import enable_ansi_support, terminal_supports_colors

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
from techlock.common.api.flask import enum_to_properties
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db
from techlock.compas.models import compliance, compliance_task

from techlock.compas.models.report import ReportSchema

from ..models.int_enum import IntEnum

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
STAGE = os.environ.get('STAGE', 'dev').upper()


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
    name = mf.String(allow_none=True, description='Used to filter compliances_timeline by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceTimelineListQueryParameters(**data)


class ComplianceTimeline(BaseModel):
    __tablename__ = 'compliances_timeline'

    compliance_id = db.Column(db.Integer,
                              db.ForeignKey('compliances.id'),
                              nullable=False)
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

