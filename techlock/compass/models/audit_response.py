from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from techlock.compass.models.report_version import Compliance

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


class AuditResponseSchema(BaseModelSchema):
    audit_id = mf.String(required=True, allow_none=False)
    instruction_id = mf.String(required=True, allow_none=False)
    compliance = EnumField(Compliance, required=True, allow_none=False)

    audit = mf.Nested('AuditSchema', dump_only=True)
    instruction = mf.Nested('ReportInstructionSchema', dump_only=True)


class AuditResponsePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditResponseSchema, many=True, dump_only=True)


class AuditResponseListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter audit_responses by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditResponseListQueryParameters(**data)


class AuditResponse(BaseModel):
    __tablename__ = 'audit_responses'

    audit_id = sa.Column(UUID, sa.ForeignKey("audits.id"), nullable=False)
    instruction_id = sa.Column(UUID, sa.ForeignKey("report_instructions.id"), nullable=False)
    compliance = sa.Column(st.Enum(Compliance), nullable=False, default=Compliance.pending)

    audit = relationship('Audit')
    instruction = relationship('ReportInstruction')


@dataclass
class AuditResponseListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditResponse
