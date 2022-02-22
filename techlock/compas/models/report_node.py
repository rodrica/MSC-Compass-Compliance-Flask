from json import dump
import os
import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from pkg_resources import require

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import backref
from sqlalchemy.orm.decl_api import declared_attr
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool
from sqlalchemy.sql.elements import True_
from sqlalchemy.sql.schema import PrimaryKeyConstraint

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compas.models.report import ReportSchema
from techlock.compas.models.report_version import ReportVersionSchema

from ..models.int_enum import IntEnum

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
STAGE = os.environ.get('STAGE', 'dev').upper()


class ReportNodeSchema(BaseModelSchema):
    text = mf.String(allow_none=True)
    number = mf.String(allow_none=True)
    row = mf.Integer(allow_none=True)
    table = mf.Integer(allow_none=True)

    parent_id = mf.Integer(allow_none=True)
    version_id = mf.Integer(required=True, allow_none=False)

    parent = mf.Nested('ReportNodeSchema', dump_only=True, exclude=('children',))
    children = mf.Nested('ReportNodeSchema', many=True, exclude=('parent',), dump_only=True)

    version = mf.Nested(ReportVersionSchema, dump_only=True, exclude=('nodes',))


class ReportNodePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(ReportNodeSchema, many=True, dump_only=True)


class ReportNodeListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter report_nodes by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return ReportNodeListQueryParameters(**data)


class ReportNode(BaseModel):
    __tablename__ = 'report_nodes'

    entity_id = db.Column('id', db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=True)
    number = db.Column(db.String, nullable=True)
    row = db.Column(db.Integer, nullable=True)
    table = db.Column(db.Integer, nullable=True)

    parent_id = db.Column(db.Integer, db.ForeignKey('report_nodes.id'), nullable=True)
    version_id = db.Column(db.Integer, db.ForeignKey('report_versions.id'))

    parent = db.relationship(
        'ReportNode',
        remote_side=[entity_id],
        back_populates='children'
    )

    children = db.relationship(
        'ReportNode',
        back_populates='parent'
    )

    version = db.relationship(
        'ReportVersion',
        back_populates='nodes'
    )


@dataclass
class ReportNodeListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = ReportNode
