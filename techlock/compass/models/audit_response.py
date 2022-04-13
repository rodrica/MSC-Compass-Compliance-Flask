import os
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compass.models.report_version import Compliance

from ..models.int_enum import IntEnum

__all__ = [
    'AuditResponse',
    'AuditResponseSchema',
    'AuditResponsePageableSchema',
    'AuditResponseListQueryParameters',
    'AuditResponseListQueryParametersSchema',
    'AUDIT_RESPONSE_CLAIM_SPEC',
]


AUDIT_RESPONSE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='audit_responses',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class AuditResponseSchema(BaseModelSchema):
    audit_id = mf.Integer(required=True, allow_none=False)
    instruction_id = mf.Integer(required=True, allow_none=False)
    compliance = EnumField(Compliance, required=True, allow_none=False)

    audit = mf.Nested('AuditSchema', dump_only=True)
    instruction = mf.Nested('ReportInstructionSchema', dump_only=True)


class AuditResponsePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditResponseSchema, many=True, dump_only=True)


class AuditResponseListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter audit_responses by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditResponseListQueryParameters(**data)


class AuditResponse(BaseModel):
    __tablename__ = 'audit_responses'

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"),
                         nullable=False)
    instruction_id = db.Column(db.Integer,
                               db.ForeignKey("report_instructions.id"),
                               nullable=False)
    compliance = db.Column(IntEnum(Compliance),
                           nullable=False,
                           default=Compliance.pending)

    audit = db.relationship('Audit')
    instruction = db.relationship('ReportInstruction')


@dataclass
class AuditResponseListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditResponse
