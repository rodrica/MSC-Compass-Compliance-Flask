from json import dump
import os
import enum
from dataclasses import dataclass
from sys import audit
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
from techlock.compas.models.report_version import Compliance
from techlock.compas.routes import compliances


__all__ = [
    'SummaryNote',
    'SummaryNoteSchema',
    'SummaryNotePageableSchema',
    'SummaryNoteListQueryParameters',
    'SummaryNoteListQueryParametersSchema',
    'SUMMARY_NOTE_CLAIM_SPEC',
]


SUMMARY_NOTE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='summary_notes',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)

STAGE = os.environ.get('STAGE', 'dev').upper()


class SummaryNoteSchema(BaseModelSchema):
    audit_id = mf.Integer(allow_none=True)

    compliance_id = mf.Integer(allow_none=True)

    audit = mf.Nested('AuditSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)


class SummaryNotePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(SummaryNoteSchema, many=True, dump_only=True)


class SummaryNoteListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter summary_notes by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return SummaryNoteListQueryParameters(**data)


class SummaryNote(BaseModel):
    __tablename__ = 'summary_notes'

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"))

    compliance_id= db.Column(db.Integer, db.ForeignKey("compliances.id"))

    audit = db.relationship('Audit')

    compliance = db.relationship('Compliance')


@dataclass
class SummaryNoteListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = SummaryNote
