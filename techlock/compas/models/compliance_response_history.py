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
from techlock.compas.models import compliance_response

from techlock.compas.models.report import ReportSchema
from techlock.compas.models.compliance_response import Phase, Status

from ..models.int_enum import IntEnum

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
STAGE = os.environ.get('STAGE', 'dev').upper()


class ComplianceResponseHistorySchema(BaseModelSchema):
    entity_id = mf.Integer(dump_only=True)
    compliance_response_id = mf.Integer(dump_only=True)
    compliance_id = mf.Integer(requird=True, allow_null=False)
    period_id = mf.Integer(requird=True, allow_null=False)
    phase = EnumField(Phase, requird=True, allow_null=False)
    status = EnumField(Status, requird=True, allow_null=False)


class ComplianceResponseHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceResponseHistorySchema, many=True, dump_only=True)


class ComplianceResponseHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter compliance_responses_history by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceResponseHistoryListQueryParameters(**data)


class ComplianceResponseHistory(BaseModel):
    __tablename__ = 'compliance_responses_history'

    entity_id = db.Column('history_id', db.Integer, primary_key=True)
    compliance_response_id = db.Column('id', db.Integer)
    compliance_id = db.Column(db.Integer,
                              db.ForeignKey('compliances.id'),
                              nullable=False)
    period_id = db.Column(db.Integer,
                          db.ForeignKey('compliance_periods.id'),
                          nullable=False)
    phase = db.Column(IntEnum(Phase), nullable=False)
    status = db.Column(IntEnum(Status), nullable=False)


@dataclass
class ComplianceResponseHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceResponseHistory

