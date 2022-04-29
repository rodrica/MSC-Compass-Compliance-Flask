from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
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


class SummaryNoteSchema(BaseModelSchema):
    audit_id = mf.String(allow_none=True)

    compliance_id = mf.String(allow_none=True)

    audit = mf.Nested('AuditSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)


class SummaryNotePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(SummaryNoteSchema, many=True, dump_only=True)


class SummaryNoteListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter summary_notes by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return SummaryNoteListQueryParameters(**data)


class SummaryNote(BaseModel):
    __tablename__ = 'summary_notes'

    audit_id = sa.Column(UUID, sa.ForeignKey("audits.id"))

    compliance_id = sa.Column(UUID, sa.ForeignKey("compliances.id"))

    audit = relationship('Audit')

    compliance = relationship('Compliance')


@dataclass
class SummaryNoteListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = SummaryNote
