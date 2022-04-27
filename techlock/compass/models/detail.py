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


class DetailSchema(BaseModelSchema):
    code = mf.String(requird=True, allow_null=False)

    compliant_until = mf.Date(allow_none=True)
    timestamp = mf.DateTime(requird=True, allow_null=False)
    timezone = mf.String(requird=True, allow_null=False)


class DetailPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(DetailSchema, many=True, dump_only=True)


class DetailListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter details by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return DetailListQueryParameters(**data)


class Detail(BaseModel):
    __tablename__ = 'details'

    code = db.Column(db.String, nullable=False)

    compliant_until = db.Column(db.Date, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)
    timezone = db.Column(
        db.String,
        nullable=False,
    )


@dataclass
class DetailListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Detail
