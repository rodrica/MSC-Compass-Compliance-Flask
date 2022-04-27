from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

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
    name = mf.String(
        allow_none=True,
        description='Used to filter journals by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return JournalListQueryParameters(**data)


class Journal(BaseModel):
    __tablename__ = 'journals'

    audit_id = sa.Column(st.Integer, sa.ForeignKey("audits.id"))
    audit_instruction_id = sa.Column(
        st.Integer,
        sa.ForeignKey("report_instructions.id"),
    )

    compliance_id = sa.Column(st.Integer, sa.ForeignKey("compliances.id"))
    compliance_period_id = sa.Column(
        st.Integer,
        sa.ForeignKey("compliance_periods.id"),
    )

    audit = relationship('Audit')
    audit_instruction = relationship('ReportInstruction')

    compliance = relationship('Compliance')
    compliance_period = relationship('CompliancePeriod')


@dataclass
class JournalListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Journal
