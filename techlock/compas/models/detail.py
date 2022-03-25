from json import dump
import os
import enum
from dataclasses import dataclass
from humanfriendly.terminal import enable_ansi_support

import marshmallow as ma
import marshmallow.fields as mf
from marshmallow_enum import EnumField
from pkg_resources import require

from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.pool.impl import FallbackAsyncAdaptedQueuePool
from sqlalchemy.sql.elements import True_
from sqlalchemy.sql.operators import nulls_last_op

from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.api.flask import enum_to_properties
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db

from techlock.compas.models.report import ReportSchema

from ..models.int_enum import IntEnum

__all__ = [
    'Detail',
    'DetailSchema',
    'DetailPageableSchema',
    'DetailListQueryParameters',
    'DetailListQueryParametersSchema',
    'DETAIL_CLAIM_SPEC',
]


DETAIL_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='details',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)
STAGE = os.environ.get('STAGE', 'dev').upper()


class DetailSchema(BaseModelSchema):
    code = mf.String(requird=True, allow_null=False)

    compliant_until = mf.Date(allow_none=True)
    timestamp = mf.DateTime(requird=True, allow_null=False)
    timezone = mf.String(requird=True, allow_null=False)


class DetailPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(DetailSchema, many=True, dump_only=True)


class DetailListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True, description='Used to filter details by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return DetailListQueryParameters(**data)


class Detail(BaseModel):
    __tablename__ = 'details'

    code = db.Column(db.String, nullable=False)

    compliant_until = db.Column(db.Date, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)
    timezone = db.Column(db.String,
                         nullable=False)


@dataclass
class DetailListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Detail

