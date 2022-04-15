from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField

from sqlalchemy.dialects.postgresql import ARRAY, UUID

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compass.models.report_version import Tag

from ..models.int_enum import IntEnum

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

    version_id = mf.Integer(required=True, allow_none=False)
    node_id = mf.Integer(required=True, allow_none=False)

    version = mf.Nested('ReportVersionSchema', dump_only=True)
    node = mf.Nested('ReportNodeSchema', dump_only=True)


class ReportInstructionPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportInstructionSchema, many=True, dump_only=True)


class ReportInstructionListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter report_instructions by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportInstructionListQueryParameters(**data)


class ReportInstruction(BaseModel):
    __tablename__ = 'report_instructions'

    uuid = db.Column(UUID(as_uuid=True), nullable=False)
    name = db.Column(db.String, nullable=True)
    text = db.Column(db.String)
    number = db.Column(db.String)
    priority = db.Column(db.Integer)
    tag = db.Column(IntEnum(Tag), nullable=True)
    mappings = db.Column(ARRAY(db.Integer), nullable=False)
    notice = db.Column(db.Boolean, default=False)
    hidden = db.Column(db.Boolean, default=False)
    row = db.Column(db.Integer)
    table = db.Column(db.Integer)

    version_id = db.Column(db.Integer, db.ForeignKey('report_versions.id'))
    node_id = db.Column(db.Integer, db.ForeignKey('report_nodes.id'))

    version = db.relationship(
        'ReportVersion',
    )

    node = db.relationship(
        'ReportNode',
        backref='instructions'
    )


@dataclass
class ReportInstructionListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportInstruction
