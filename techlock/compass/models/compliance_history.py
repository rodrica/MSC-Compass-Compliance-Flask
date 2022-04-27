from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import ARRAY
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from ..models.compliance import Plan
from ..models.int_enum import IntEnum

__all__ = [
    'ComplianceHistory',
    'ComplianceHistorySchema',
    'ComplianceHistoryPageableSchema',
    'ComplianceHistoryListQueryParameters',
    'ComplianceHistoryListQueryParametersSchema',
    'COMPLIANCE_HISTORY_CLAIM_SPEC',
]


COMPLIANCE_HISTORY_CLAIM_SPEC = ClaimSpec(
    actions=[
        'read',
    ],
    resource_name='compliances_history',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class ComplianceHistorySchema(BaseModelSchema):
    entity_id = mf.Integer(dump_only=True)
    compliance_id = mf.Integer()
    user_id = mf.String(require=True, allow_none=False)
    tasks = mf.List(mf.Integer, require=True, allow_none=False)
    start_date = mf.Date(require=True, allow_none=False)
    end_date = mf.Date(required=True, allow_none=False)
    plan = EnumField(Plan, require=True, allow_none=False)


class ComplianceHistoryPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceHistorySchema, many=True, dump_only=True)


class ComplianceHistoryListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliances_history by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceHistoryListQueryParameters(**data)


class ComplianceHistory(BaseModel):
    __tablename__ = 'compliances_history'

    entity_id = sa.Column('history_id', st.Integer, primary_key=True)
    audit_id = sa.Column('id', st.Integer)
    user_id = sa.Column(st.String, nullable=False)
    tasks = sa.Column(ARRAY(st.Integer), nullable=False)
    start_date = sa.Column(st.Date, nullable=False)
    end_date = sa.Column(st.Date, nullable=False)
    plan = sa.Column(IntEnum(Plan), nullable=False)


@dataclass
class ComplianceHistoryListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ComplianceHistory
