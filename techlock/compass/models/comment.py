from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

__all__ = [
    'Comment',
    'CommentSchema',
    'CommentPageableSchema',
    'CommentListQueryParameters',
    'CommentListQueryParametersSchema',
    'COMMENT_CLAIM_SPEC',
]


COMMENT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='comments',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class CommentSchema(BaseModelSchema):
    audit_id = mf.String(allow_none=True)
    audit_instruction_id = mf.String(allow_none=True)

    compliance_id = mf.String(allow_none=True)
    compliance_period_id = mf.String(allow_none=True)

    timestamp = mf.DateTime(requird=True, allow_null=False)

    audit = mf.Nested('AuditSchema', dump_only=True)
    audit_instruction = mf.Nested('ReportInstructionSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    compliance_period = mf.Nested('CompliancePeriodSchema', dump_only=True)


class CommentPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(CommentSchema, many=True, dump_only=True)


class CommentListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter comments by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return CommentListQueryParameters(**data)


class Comment(BaseModel):
    __tablename__ = 'comments'

    audit_id = sa.Column(UUID, sa.ForeignKey("audits.id"))
    audit_instruction_id = sa.Column(UUID, sa.ForeignKey("report_instructions.id"))
    compliance_id = sa.Column(UUID, sa.ForeignKey("compliances.id"))
    compliance_period_id = sa.Column(UUID, sa.ForeignKey("compliance_periods.id"))

    timestamp = sa.Column(st.TIMESTAMP, nullable=False)

    audit = relationship('Audit')
    audit_instruction = relationship('ReportInstruction')

    compliance = relationship('Compliance')
    compliance_period = relationship('CompliancePeriod')


@dataclass
class CommentListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Comment
