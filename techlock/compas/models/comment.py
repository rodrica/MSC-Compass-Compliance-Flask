import os
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db


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

STAGE = os.environ.get('STAGE', 'dev').upper()


class CommentSchema(BaseModelSchema):
    user_id = mf.String(require=True, allow_none=False)

    audit_id = mf.Integer(allow_none=True)
    audit_instruction_id = mf.Integer(allow_none=True)

    compliance_id = mf.Integer(allow_none=True)
    compliance_period_id = mf.Integer(allow_none=True)

    timestamp = mf.DateTime(requird=True, allow_null=False)

    audit = mf.Nested('AuditSchema', dump_only=True)
    audit_instruction = mf.Nested('ReportInstructionSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    compliance_period = mf.Nested('CompliancePeriodSchema', dump_only=True)


class CommentPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(CommentSchema, many=True, dump_only=True)


class CommentListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter comments by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return CommentListQueryParameters(**data)


class Comment(BaseModel):
    __tablename__ = 'comments'

    user_id = db.Column(db.String, nullable=False)

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"))

    audit_instruction_id = db.Column(db.Integer,
                                     db.ForeignKey("report_instructions.id"))

    compliance_id= db.Column(db.Integer, db.ForeignKey("compliances.id"))
    compliance_period_id= db.Column(db.Integer,
                                    db.ForeignKey("compliance_periods.id"))

    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    audit = db.relationship('Audit')
    audit_instruction = db.relationship('ReportInstruction')

    compliance = db.relationship('Compliance')
    compliance_period = db.relationship('CompliancePeriod')


@dataclass
class CommentListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Comment
