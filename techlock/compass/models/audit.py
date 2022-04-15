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
    'Audit',
    'AuditSchema',
    'AuditPageableSchema',
    'AuditListQueryParameters',
    'AuditListQueryParametersSchema',
    'AUDIT_CLAIM_SPEC',
]


AUDIT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='audits',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class Phase(enum.Enum):
    scoping_and_validation = 0
    policy_and_procedure_review = 1
    audit = 2
    remediation = 3
    qa_review = 4
    project_close_out = 5
    billing_and_marketing = 6
    archived = 7


class AuditSchema(BaseModelSchema):
    user_id = mf.String()
    reports = mf.List(mf.Integer)
    start_date = mf.Date()
    estimated_remediation_date = mf.Date()
    remediation_date = mf.Date(required=True, allow_none=False)
    estimated_end_date = mf.Date()
    end_date = mf.Date(required=True, allow_none=False)
    phase = EnumField(Phase, default=Phase.scoping_and_validation)


class AuditPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(AuditSchema, many=True, dump_only=True)


class AuditListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter audits by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return AuditListQueryParameters(**data)


class Audit(BaseModel):
    __tablename__ = 'audits'

    user_id = db.Column(db.String)
    reports = db.Column(ARRAY(db.Integer))
    start_date = db.Column(db.Date)
    estimated_remediation_date = db.Column(db.Date)
    remediation_date = db.Column(db.Date)
    estimated_end_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    phase = db.Column(IntEnum(Phase), default=Phase.scoping_and_validation)


@dataclass
class AuditListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Audit
