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

from techlock.compas.models.report import ReportSchema

from ..models.int_enum import IntEnum

__all__ = [
    'Compliance',
    'ComplianceSchema',
    'CompliancePageableSchema',
    'ComplianceListQueryParameters',
    'ComplianceListQueryParametersSchema',
    'COMPLIANCE_CLAIM_SPEC',
]


COMPLIANCE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliances',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class Plan(enum.Enum):
    bronze = 0
    silver = 1
    gold = 2
    platinum = 3


class ComplianceSchema(BaseModelSchema):
    user_id = mf.String()
    reports = mf.List(mf.Integer)
    start_date = mf.Date()
    estimated_remediation_date = mf.Date()
    remediation_date = mf.Date(required=True, allow_none=False)
    estimated_end_date = mf.Date()
    end_date = mf.Date(required=True, allow_none=False)
    phase = EnumField(Plan, default=Plan.bronze)


class CompliancePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceSchema, many=True, dump_only=True)


class ComplianceListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter compliances by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceListQueryParameters(**data)


class Compliance(BaseModel):
    __tablename__ = 'compliances'

    user_id = db.Column(db.String)
    reports = db.Column(ARRAY(db.Integer))
    start_date = db.Column(db.Date)
    estimated_remediation_date = db.Column(db.Date)
    remediation_date = db.Column(db.Date)
    estimated_end_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    phase = db.Column(IntEnum(Plan), default=Plan.bronze)


@dataclass
class ComplianceListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Compliance

