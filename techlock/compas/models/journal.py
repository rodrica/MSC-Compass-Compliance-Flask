import os
from dataclasses import dataclass

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
from techlock.compas.models.report_version import Compliance
from techlock.compas.routes import compliances


__all__ = [
    'Journal',
    'JournalSchema',
    'JournalPageableSchema',
    'JournalListQueryParameters',
    'JournalListQueryParametersSchema',
    'JOURNAL_CLAIM_SPEC',
]


JOURNAL_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='journals',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)

STAGE = os.environ.get('STAGE', 'dev').upper()


class JournalSchema(BaseModelSchema):
    audit_id = mf.Integer(allow_none=True)
    audit_instruction_id = mf.Integer(allow_none=True)

    compliance_id = mf.Integer(allow_none=True)
    compliance_period_id = mf.Integer(allow_none=True)

    audit = mf.Nested('AuditSchema', dump_only=True)
    audit_instruction = mf.Nested('ReportInstructionSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    compliance_period = mf.Nested('CompliancePeriodSchema', dump_only=True)


class JournalPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(JournalSchema, many=True, dump_only=True)


class JournalListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter journals by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return JournalListQueryParameters(**data)


class Journal(BaseModel):
    __tablename__ = 'journals'

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"))
    audit_instruction_id = db.Column(db.Integer, db.ForeignKey("report_instructions.id"))

    compliance_id= db.Column(db.Integer, db.ForeignKey("compliances.id"))
    compliance_period_id= db.Column(db.Integer, db.ForeignKey("compliance_periods.id"))

    audit = db.relationship('Audit')
    audit_instruction = db.relationship('ReportInstruction')

    compliance = db.relationship('Compliance')
    compliance_period = db.relationship('CompliancePeriod')


@dataclass
class JournalListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Journal

