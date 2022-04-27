import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import ARRAY
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from ..models.int_enum import IntEnum

__all__ = [
    'Compliance',
    'ComplianceSchema',
    'CompliancePageableSchema',
    'ComplianceListQueryParameters',
    'ComplianceListQueryParametersSchema',
    'COMPLIANCE_CLAIM_SPEC',
]


COMPLIANCE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliances',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class Plan(enum.Enum):
    bronze = 0
    silver = 1
    gold = 2
    platinum = 3


class ComplianceSchema(BaseModelSchema):
    user_id = mf.String(require=True, allow_none=False)
    tasks = mf.List(mf.Integer, require=True, allow_none=False)
    start_date = mf.Date(require=True, allow_none=False)
    end_date = mf.Date(required=True, allow_none=False)
    plan = EnumField(Plan, require=True, allow_none=False)


class CompliancePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ComplianceSchema, many=True, dump_only=True)


class ComplianceListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter compliances by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ComplianceListQueryParameters(**data)


class Compliance(BaseModel):
    __tablename__ = 'compliances'

    user_id = db.Column(db.String, nullable=False)
    tasks = db.Column(ARRAY(db.Integer), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    plan = db.Column(IntEnum(Plan), nullable=False)


@dataclass
class ComplianceListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Compliance
