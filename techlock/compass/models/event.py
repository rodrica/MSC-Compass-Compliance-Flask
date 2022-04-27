import enum
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as st  # Prevent class name overlap.
from marshmallow_enum import EnumField
from sqlalchemy.orm import relationship
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema

from techlock.compass.models.int_enum import IntEnum

__all__ = [
    'Event',
    'EventSchema',
    'EventPageableSchema',
    'EventListQueryParameters',
    'EventListQueryParametersSchema',
    'EVENT_CLAIM_SPEC',
]


EVENT_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete',
    ],
    resource_name='events',
    filter_fields=[
        'name',
        'created_by',
    ],
    default_actions=['read'],
)


class Type(enum.Enum):
    custom = 0
    create = 1
    update = 2
    delete = 3


class Visibility(enum.Enum):
    common = 0
    internal = 1
    external = 2


class EventSchema(BaseModelSchema):
    user_id = mf.String(allow_none=True)

    audit_id = mf.Integer(allow_none=True)
    audit_instruction_id = mf.Integer(allow_none=True)

    compliance_id = mf.Integer(allow_none=True)
    compliance_period_id = mf.Integer(allow_none=True)

    timestamp = mf.DateTime(requird=True, allow_none=False)
    type = EnumField(Type, required=True, allow_none=False)
    visibility = EnumField(Visibility, required=True, allow_none=False)

    audit = mf.Nested('AuditSchema', dump_only=True)
    audit_instruction = mf.Nested('ReportInstructionSchema', dump_only=True)

    compliance = mf.Nested('ComplianceSchema', dump_only=True)
    compliance_period = mf.Nested('CompliancePeriodSchema', dump_only=True)


class EventPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(EventSchema, many=True, dump_only=True)


class EventListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    name = mf.String(
        allow_none=True,
        description='Used to filter events by name prefix.',
    )

    @ma.post_load
    def make_object(self, data, **kwargs):
        return EventListQueryParameters(**data)


class Event(BaseModel):
    __tablename__ = 'events'

    user_id = sa.Column(st.String, nullable=True)

    audit_id = sa.Column(st.Integer, sa.ForeignKey("audits.id"))

    audit_instruction_id = sa.Column(
        st.Integer,
        sa.ForeignKey("report_instructions.id"),
    )

    compliance_id = sa.Column(st.Integer, sa.ForeignKey("compliances.id"))
    compliance_period_id = sa.Column(
        st.Integer,
        sa.ForeignKey("compliance_periods.id"),
    )

    timestamp = sa.Column(st.TIMESTAMP, nullable=False)
    type = sa.Column(IntEnum(Type), nullable=False)
    visibility = sa.Column(IntEnum(Visibility), nullable=False)

    audit = relationship('Audit')
    audit_instruction = relationship('ReportInstruction')

    compliance = relationship('Compliance')
    compliance_period = relationship('CompliancePeriod')


@dataclass
class EventListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Event
