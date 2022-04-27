import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from techlock.compass.models.report import ReportSchema

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
    report_id = mf.String(allow_none=True, required=False)

    nodes = mf.Nested(
        'ReportNodeSchema',
        dump_only=True,
        many=True,
        exclude=('version',),
    )


class ReportVersionPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportVersionSchema, many=True, dump_only=True)


class ReportVersionListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter report_versions by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportVersionListQueryParameters(**data)


class ReportVersion(BaseModel):
    __tablename__ = 'report_versions'

    uuid = sa.Column(UUID(as_uuid=True), nullable=False)
    component = sa.Column(st.String, nullable=False)
    template = sa.Column(st.String)
    processor = sa.Column(st.String)
    mapped = sa.Column(st.Boolean, nullable=False)
    compliance_only = sa.Column(st.Boolean, nullable=False)
    compliance_options = sa.Column(ARRAY(st.Enum(Compliance)), nullable=False)
    highest_priority = sa.Column(st.Integer, nullable=False)
    tag_options = sa.Column(ARRAY(st.Enum(Tag)), nullable=False)
    default_navigation = sa.Column(st.Integer)
    section_regex = sa.Column(st.String)
    column_mapping = sa.Column(ARRAY(st.Integer, dimensions=2), nullable=False)
    tlc_header = sa.Column(st.String)
    tlc_position = sa.Column(st.Integer)

    report_id = sa.Column(UUID, sa.ForeignKey('reports.id'))

    report = relationship(
        'Report',
        back_populates='versions',
    )

    nodes = relationship(
        'ReportNode',
        back_populates='version',
    )


@dataclass
class ReportVersionListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportVersion
