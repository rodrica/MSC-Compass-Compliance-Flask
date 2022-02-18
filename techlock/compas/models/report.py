import os
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from sqlalchemy.dialects.postgresql import JSONB
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    Claim,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

__all__ = [
    'Report',
    'ReportSchema',
    'ReportPageableSchema',
    'ReportListQueryParameters',
    'ReportListQueryParametersSchema',
    'REPORT_CLAIM_SPEC',
]


REPORT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='reports',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class ReportSchema(BaseModelSchema):
    pass


class ReportPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportSchema, many=True, dump_only=True)


class ReportListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter reports by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportListQueryParameters(**data)


class Report(BaseModel):
    __tablename__ = 'reports'


@dataclass
class ReportListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Report