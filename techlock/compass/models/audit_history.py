from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

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


class AuditHistorySchema(BaseModelSchema):
    audit_id = mf.String()
    auditor = mf.String()
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
    name = mf.String(
        allow_none=True,
        description='Used to filter audits_history by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditHistoryListQueryParameters(**data)


class AuditHistory(BaseModel):
    __tablename__ = 'audits_history'

    audit_id = sa.Column(UUID, sa.ForeignKey("audits.id"))
    auditor = sa.Column(st.String)
    reports = sa.Column(ARRAY(st.Integer))
    start_date = sa.Column(st.Date)
    estimated_remediation_date = sa.Column(st.Date)
    remediation_date = sa.Column(st.Date)
    estimated_end_date = sa.Column(st.Date)
    end_date = sa.Column(st.Date)
    phase = sa.Column(st.Enum(Phase), default=Phase.scoping_and_validation)


@dataclass
class AuditHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = AuditHistory
