from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from techlock.compass.models.report_version import ReportVersionSchema

__all__ = [
    'ReportNode',
    'ReportNodeSchema',
    'ReportNodePageableSchema',
    'ReportNodeListQueryParameters',
    'ReportNodeListQueryParametersSchema',
    'REPORT_NODE_CLAIM_SPEC',
]


REPORT_NODE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='report_nodes',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class ReportNodeSchema(BaseModelSchema):
    text = mf.String(allow_none=True)
    number = mf.String(allow_none=True)
    row = mf.Integer(allow_none=True)
    table = mf.Integer(allow_none=True)

    parent_id = mf.String(allow_none=True)
    version_id = mf.String(required=True, allow_none=False)

    parent = mf.Nested(
        'ReportNodeSchema',
        dump_only=True,
        exclude=('children',),
    )

    children = mf.Nested(
        'ReportNodeSchema',
        many=True,
        exclude=('parent',),
        dump_only=True,
    )

    version = mf.Nested(
        ReportVersionSchema,
        dump_only=True,
        exclude=('nodes',),
    )


class ReportNodePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportNodeSchema, many=True, dump_only=True)


class ReportNodeListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter report_nodes by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportNodeListQueryParameters(**data)


class ReportNode(BaseModel):
    __tablename__ = 'report_nodes'

    text = sa.Column(st.String, nullable=True)
    number = sa.Column(st.String, nullable=True)
    row = sa.Column(st.Integer, nullable=True)
    table = sa.Column(st.Integer, nullable=True)

    parent_id = sa.Column(UUID, sa.ForeignKey('report_nodes.id'), nullable=True)
    version_id = sa.Column(UUID, sa.ForeignKey('report_versions.id'))

    parent = relationship(
        'ReportNode',
        remote_side=['entity_id'],
        back_populates='children',
    )

    children = relationship(
        'ReportNode',
        back_populates='parent',
    )

    version = relationship(
        'ReportVersion',
        back_populates='nodes',
    )


@dataclass
class ReportNodeListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportNode
