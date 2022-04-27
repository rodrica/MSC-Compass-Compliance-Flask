from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

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
    name = mf.String(
        allow_none=True,
        description='Used to filter uploads by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return UploadListQueryParameters(**data)


class Upload(BaseModel):
    __tablename__ = 'uploads'

    user_id = sa.Column(st.String, nullable=False)

    audit_id = sa.Column(st.Integer, sa.ForeignKey("audits.id"))

    compliance_id = sa.Column(st.Integer, sa.ForeignKey("compliances.id"))
    compliance_period_id = sa.Column(
        st.Integer,
        sa.ForeignKey("compliance_periods.id"),
    )

    timestamp = sa.Column(st.TIMESTAMP, nullable=False)

    audit_evidence = sa.Column(st.Boolean, unique=False)
    uuid = sa.Column(st.String, nullable=False)

    audit = relationship('Audit')

    compliance = relationship('Compliance')
    compliance_period = relationship('CompliancePeriod')


@dataclass
class UploadListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Upload
