from json import dump
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
from techlock.common.api.flask import enum_to_properties
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db
from techlock.compas.models import compliance

from techlock.compas.models.report import ReportSchema

from ..models.int_enum import IntEnum
from ..models.compliance import Plan

__all__ = [
    'ComplianceHistory',
    'ComplianceHistorySchema',
    'ComplianceHistoryPageableSchema',
    'ComplianceHistoryListQueryParameters',
    'ComplianceHistoryListQueryParametersSchema',
    'COMPLIANCE_HISTORY_CLAIM_SPEC',
]


COMPLIANCE_HISTORY_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read'
    ],
    resource_name='compliances_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class ComplianceHistorySchema(BaseModelSchema):
    entity_id = mf.Integer(dump_only=True)
    compliance_id = mf.Integer()
    user_id = mf.String(require=True, allow_none=False)
    tasks = mf.List(mf.Integer, require=True, allow_none=False)
    start_date = mf.Date(require=True, allow_none=False)
    end_date = mf.Date(required=True, allow_none=False)
    plan = EnumField(Plan, require=True, allow_none=False)


class ComplianceHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceHistorySchema, many=True, dump_only=True)


class ComplianceHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter compliances_history by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceHistoryListQueryParameters(**data)


class ComplianceHistory(BaseModel):
    __tablename__ = 'compliances_history'

    entity_id = db.Column('history_id', db.Integer, primary_key=True)
    audit_id = db.Column('id', db.Integer)
    user_id = db.Column(db.String, nullable=False)
    tasks = db.Column(ARRAY(db.Integer), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    plan = db.Column(IntEnum(Plan), nullable=False)


@dataclass
class ComplianceHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceHistory

