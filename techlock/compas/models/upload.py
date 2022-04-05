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
    'Upload',
    'UploadSchema',
    'UploadPageableSchema',
    'UploadListQueryParameters',
    'UploadListQueryParametersSchema',
    'UPLOAD_CLAIM_SPEC',
]


UPLOAD_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='uploads',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)

STAGE = os.environ.get('STAGE', 'dev').upper()


class UploadSchema(BaseModelSchema):
    user_id = mf.String(require=True, allow_none=False)

    audit_id = mf.Integer(allow_none=True)

    compliance_id = mf.Integer(allow_none=True)
    compliance_period_id = mf.Integer(allow_none=True)

    timestamp = mf.DateTime(requird=True, allow_none=False)

    audit_evidence = mf.Boolean(allow_none=True)
    uuid = mf.String(requird=True, allow_none=False)

    audit = mf.Nested('AuditSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    compliance_period = mf.Nested('CompliancePeriodSchema', dump_only=True)


class UploadPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(UploadSchema, many=True, dump_only=True)


class UploadListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(allow_none=True,
                     description='Used to filter uploads by name prefix.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return UploadListQueryParameters(**data)


class Upload(BaseModel):
    __tablename__ = 'uploads'

    user_id = db.Column(db.String, nullable=False)

    audit_id = db.Column(db.Integer, db.ForeignKey("audits.id"))

    compliance_id= db.Column(db.Integer, db.ForeignKey("compliances.id"))
    compliance_period_id= db.Column(db.Integer,
                                    db.ForeignKey("compliance_periods.id"))

    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    audit_evidence = db.Column(db.Boolean, unique=False)
    uuid = db.Column(db.String, nullable=False)

    audit = db.relationship('Audit')

    compliance = db.relationship('Compliance')
    compliance_period = db.relationship('CompliancePeriod')


@dataclass
class UploadListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Upload
