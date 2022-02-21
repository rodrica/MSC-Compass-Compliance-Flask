from json import dump
import os
import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from pkg_resources import require

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compas.models.report import ReportSchema

from ..models.int_enum import IntEnum

__all__ = [
    'ReportVersion',
    'ReportVersionSchema',
    'ReportVersionPageableSchema',
    'ReportVersionListQueryParameters',
    'ReportVersionListQueryParametersSchema',
    'REPORT_VERSION_CLAIM_SPEC',
]


REPORT_VERSION_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='report_versions',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class Tag(enum.Enum):
    technical = 0
    documentation = 1
    interview = 2


class Compliance(enum.Enum):
    pending = 0
    in_place = 1
    in_place_with_ccw = 2
    not_applicable = 3
    not_tested = 4
    not_in_place = 5
    satisfactory = 6
    other_than_satisfactory = 7


class ReportVersionSchema(BaseModelSchema):
    uuid = mf.String(requird=True, help="")
    component = mf.String(requird=True, help="")
    template = mf.String(help="")
    processor = mf.String(help="")
    mapped = mf.Boolean(requird=True, help="")
    compliance_only = mf.Boolean(requird=True, help="")
    compliance_options = mf.List(EnumField(Compliance), requird=True)
    highest_priority = mf.Integer(requird=True, help="")
    tag_options = mf.List(EnumField(Tag), requird=True)
    default_navigation = mf.Integer(required=False, allow_none=True, help="")
    section_regex = mf.String(required=False, allow_none=True, help="")
    column_mapping = mf.List(mf.List(mf.Integer(), requird=True))
    tlc_header = mf.String(help="")
    tlc_position = mf.Integer(help="")

    report = mf.Nested(ReportSchema, dump_only=True)
    report_id = mf.Integer(allow_none=True, required=False)


class ReportVersionPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportVersionSchema, many=True, dump_only=True)


class ReportVersionListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter report_versions by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportVersionListQueryParameters(**data)


class ReportVersion(BaseModel):
    __tablename__ = 'report_versions'

    uuid = db.Column(UUID(as_uuid=True), nullable=False)
    component = db.Column(db.String, nullable=False)
    template = db.Column(db.String)
    processor = db.Column(db.String)
    mapped = db.Column(db.Boolean, nullable=False)
    compliance_only = db.Column(db.Boolean, nullable=False)
    compliance_options = db.Column(ARRAY(IntEnum(Compliance)), nullable=False)
    highest_priority = db.Column(db.Integer, nullable=False)
    tag_options = db.Column(db.ARRAY(IntEnum(Tag)), nullable=False)
    default_navigation = db.Column(db.Integer)
    section_regex = db.Column(db.String)
    column_mapping = db.Column(ARRAY(db.Integer, dimensions=2), nullable=False)
    tlc_header = db.Column(db.String)
    tlc_position = db.Column(db.Integer)

    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'))

    report = db.relationship(
        'Report',
        back_populates='versions'
    )
    #has_many :nodes, Noddump_only=True, e


@dataclass
class ReportVersionListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportVersion
