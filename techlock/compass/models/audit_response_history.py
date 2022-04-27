from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from techlock.compass.models.report_version import Compliance

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
        'read',
    ],
    resource_name='audit_responses_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


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
    name = mf.String(
        allow_none=True,
        description='Used to filter audit_responses_history by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditResponseHistoryListQueryParameters(**data)


class AuditResponseHistory(BaseModel):
    __tablename__ = 'audit_responses_history'

    entity_id = sa.Column('history_id', st.Integer, primary_key=True)
    audit_response_id = sa.Column('id', st.Integer)
    audit_id = sa.Column(
        st.Integer, sa.ForeignKey("audits.id"),
        nullable=False,
    )
    instruction_id = sa.Column(
        st.Integer,
        sa.ForeignKey("report_instructions.id"),
        nullable=False,
    )
    compliance = sa.Column(
        IntEnum(Compliance),
        nullable=False,
        default=Compliance.pending,
    )

    audit = relationship('Audit')
    instruction = relationship('ReportInstruction')


@dataclass
class AuditResponseHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditResponseHistory
