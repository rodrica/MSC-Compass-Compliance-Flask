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

from techlock.compass.models.report_version import Tag

__all__ = [
    'ReportInstruction',
    'ReportInstructionSchema',
    'ReportInstructionPageableSchema',
    'ReportInstructionListQueryParameters',
    'ReportInstructionListQueryParametersSchema',
    'REPORT_INSTRUCTION_CLAIM_SPEC',
]


REPORT_INSTRUCTION_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='report_instructions',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class ReportInstructionSchema(BaseModelSchema):
    uuid = mf.String(required=True, allow_none=False)
    name = mf.String(allow_none=True)
    text = mf.String(allow_none=True)
    number = mf.String(allow_none=True)
    priority = mf.Integer(allow_none=True)
    tag = EnumField(Tag, allow_none=True, required=False)
    mappings = mf.List(mf.Integer(), allow_none=False, required=True)
    notice = mf.Boolean(default=False)
    hidden = mf.Boolean(default=False)
    row = mf.Integer(allow_none=True, required=False)
    table = mf.Integer(allow_none=True, required=False)

    version_id = mf.String(required=True, allow_none=False)
    node_id = mf.String(required=True, allow_none=False)

    version = mf.Nested('ReportVersionSchema', dump_only=True)
    node = mf.Nested('ReportNodeSchema', dump_only=True)


class ReportInstructionPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportInstructionSchema, many=True, dump_only=True)


class ReportInstructionListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter report_instructions by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportInstructionListQueryParameters(**data)


class ReportInstruction(BaseModel):
    __tablename__ = 'report_instructions'

    uuid = sa.Column(UUID(as_uuid=True), nullable=False)
    name = sa.Column(st.String, nullable=True)
    text = sa.Column(st.String)
    number = sa.Column(st.String)
    priority = sa.Column(st.Integer)
    tag = sa.Column(st.Enum(Tag), nullable=True)
    mappings = sa.Column(ARRAY(st.Integer), nullable=False)
    notice = sa.Column(st.Boolean, default=False)
    hidden = sa.Column(st.Boolean, default=False)
    row = sa.Column(st.Integer)
    table = sa.Column(st.Integer)

    version_id = sa.Column(UUID, sa.ForeignKey('report_versions.id'))
    node_id = sa.Column(UUID, sa.ForeignKey('report_nodes.id'))

    version = relationship('ReportVersion')

    node = relationship('ReportNode', backref='instructions')


@dataclass
class ReportInstructionListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportInstruction
