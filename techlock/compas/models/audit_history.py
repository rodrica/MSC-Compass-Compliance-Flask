import os
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField

from sqlalchemy.dialects.postgresql import ARRAY

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from ..models.int_enum import IntEnum
from .audit import Phase

__all__ = [
    'AuditHistory',
    'AuditHistorySchema',
    'AuditHistoryPageableSchema',
    'AuditHistoryListQueryParameters',
    'AuditHistoryListQueryParametersSchema',
    'AUDIT_HISTORY_CLAIM_SPEC',
]


AUDIT_HISTORY_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='audits_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class AuditHistorySchema(BaseModelSchema):
    entity_id = mf.Integer(dump_only=True)
    audit_id = mf.Integer()
    user_id = mf.String()
    reports = mf.List(mf.Integer)
    start_date = mf.Date()
    estimated_remediation_date = mf.Date()
    remediation_date = mf.Date(required=True, allow_none=False)
    estimated_end_date = mf.Date()
    end_date = mf.Date(required=True, allow_none=False)
    phase = EnumField(Phase, default=Phase.scoping_and_validation)


class AuditHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditHistorySchema, many=True, dump_only=True)


class AuditHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter audits_history by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditHistoryListQueryParameters(**data)


class AuditHistory(BaseModel):
    __tablename__ = 'audits_history'

    entity_id = db.Column('history_id', db.Integer, primary_key=True)
    audit_id = db.Column('id', db.Integer)
    user_id = db.Column(db.String)
    reports = db.Column(ARRAY(db.Integer))
    start_date = db.Column(db.Date)
    estimated_remediation_date = db.Column(db.Date)
    remediation_date = db.Column(db.Date)
    estimated_end_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    phase = db.Column(IntEnum(Phase), default=Phase.scoping_and_validation)


@dataclass
class AuditHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditHistory
