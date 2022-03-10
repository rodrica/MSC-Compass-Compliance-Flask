from importlib import import_module
from json import dump
import os
import enum
from dataclasses import dataclass

from flask_migrate import history
from humanfriendly.terminal import enable_ansi_support
from jinja2 import defaults

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from pkg_resources import require

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool
from sqlalchemy.sql.elements import True_
from sqlalchemy.sql.operators import from_, nulls_last_op
from sqlalchemy.sql.sqltypes import Integer

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compas.models.report_version import Compliance

from ..models.int_enum import IntEnum

__all__ = [
    'AuditResponseHistory',
    'AuditResponseHistorySchema',
    'AuditResponseHistoryPageableSchema',
    'AuditResponseHistoryListQueryParameters',
    'AuditResponseHistoryListQueryParametersSchema',
    'AUDIT_RESPONSE_HISTORY_CLAIM_SPEC',
]


AUDIT_RESPONSE_HISTORY_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read'
    ],
    resource_name='audit_responses_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class AuditResponseHistorySchema(BaseModelSchema):
    entity_id = mf.Integer(dump_only=True)
    audit_response_id = mf.Integer(dump_only=True)
    audit_id = mf.Integer(dump_only=True)
    instruction_id = mf.Integer(dump_only=True)
    compliance = EnumField(Compliance, dump_only=True)

    audit = mf.Nested('AuditSchema', dump_only=True)
    instruction = mf.Nested('ReportInstructionSchema', dump_only=True)


class AuditResponseHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditResponseHistorySchema, many=True, dump_only=True)


class AuditResponseHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter audit_responses_history by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditResponseHistoryListQueryParameters(**data)


class AuditResponseHistory(BaseModel):
    __tablename__ = 'audit_responses_history'

    entity_id = db.Column('history_id', db.Integer, primary_key=True)
    audit_response_id = db.Column('id', db.Integer)
    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"),
                         nullable=False)
    instruction_id = db.Column(db.Integer,
                               db.ForeignKey("report_instructions.id"),
                               nullable=False)
    compliance = db.Column(IntEnum(Compliance), nullable=False, default=Compliance.pending)
    
    audit = db.relationship('Audit')
    instruction = db.relationship('ReportInstruction')

@dataclass
class AuditResponseHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditResponseHistory

