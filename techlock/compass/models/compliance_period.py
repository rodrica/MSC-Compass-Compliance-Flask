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
    'CompliancePeriod',
    'CompliancePeriodSchema',
    'CompliancePeriodPageableSchema',
    'CompliancePeriodListQueryParameters',
    'CompliancePeriodListQueryParametersSchema',
    'COMPLIANCE_PERIOD_CLAIM_SPEC',
]


COMPLIANCE_PERIOD_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='compliance_periods',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class CompliancePeriodSchema(BaseModelSchema):
    compliance_id = mf.Integer(require=True, allow_none=False)
    task_id = mf.Integer(require=True, allow_none=False)
    start_date = mf.Date(require=True, allow_none=False)
    end_date = mf.Date(required=True, allow_none=False)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    task = mf.Nested('ComplianceTaskSchema', dump_only=True)


class CompliancePeriodPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(CompliancePeriodSchema, many=True, dump_only=True)


class CompliancePeriodListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter compliance_periods by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return CompliancePeriodListQueryParameters(**data)


class CompliancePeriod(BaseModel):
    __tablename__ = 'compliance_periods'

    compliance_id = db.Column(db.Integer,
                              db.ForeignKey('compliances.id'),
                              nullable=False)
    task_id = db.Column(db.Integer,
                        db.ForeignKey('compliance_tasks.id'),
                        nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    compliance = db.relationship('Compliance')
    task = db.relationship('ComplianceTask')


@dataclass
class CompliancePeriodListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = CompliancePeriod
