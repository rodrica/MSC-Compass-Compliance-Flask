import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass
from sqlalchemy import func as sa_fn
from sqlalchemy.dialects.postgresql import UUID

from techlock.common.api import (
    ClaimSpec,
    OffsetPageableResponseBaseSchema,
    BaseOffsetListQueryParams, BaseOffsetListQueryParamsSchema,
)
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import (
    db,
    BaseModel, BaseModelSchema,
    get_string_filter,
)

from .department import Department, DepartmentSchema

__all__ = [
    'Office',
    'OfficeSchema',
    'OfficePageableSchema',
    'OfficeListQueryParameters',
    'OfficeListQueryParametersSchema',
    'OFFICE_CLAIM_SPEC',
]


OFFICE_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='offices',
    filter_fields=[]
)


class OfficeSchema(BaseModelSchema):
    street1 = mf.String(allow_none=True)
    street2 = mf.String(allow_none=True)
    street3 = mf.String(allow_none=True)
    city = mf.String(allow_none=True)
    state = mf.String(allow_none=True)
    country = mf.String(allow_none=True)
    postal_code = mf.String(allow_none=True)
    latitude = mf.Decimal(allow_none=True)
    longitude = mf.Decimal(allow_none=True)

    departments = mf.Nested(DepartmentSchema, allow_none=True, many=True, dump_only=True)
    department_ids = mf.List(mf.UUID(), allow_none=True, required=False, load_only=True)


class OfficeListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    city = mf.String(allow_none=True, description='Used to filter offices by city prefix.')
    state = mf.String(allow_none=True, description='Used to filter offices by state prefix.')
    country = mf.String(allow_none=True, description='Used to filter offices by country prefix.')

    department_id = mf.String(allow_none=True, description='Used to filter offices by department_id.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return OfficeListQueryParameters(**data)


class OfficePageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(OfficeSchema, many=True, dump_only=True)


offices_to_departments = db.Table(
    'offices_to_departments',
    db.Column('office_id', UUID(as_uuid=True), db.ForeignKey('offices.id'), primary_key=True),
    db.Column('department_id', UUID(as_uuid=True), db.ForeignKey('departments.id'), primary_key=True)
)


class Office(BaseModel):
    __tablename__ = 'offices'

    street1 = db.Column(db.String, unique=False, nullable=True)
    street2 = db.Column(db.String, unique=False, nullable=True)
    street3 = db.Column(db.String, unique=False, nullable=True)
    city = db.Column(db.String, unique=False, nullable=True)
    state = db.Column(db.String, unique=False, nullable=True)
    country = db.Column(db.String, unique=False, nullable=True)
    postal_code = db.Column(db.String, unique=False, nullable=True)
    latitude = db.Column(db.DECIMAL(precision=12), unique=False, nullable=True)
    longitude = db.Column(db.DECIMAL(precision=12), unique=False, nullable=True)

    departments = db.relationship(
        'Department',
        secondary=offices_to_departments,
        lazy='subquery',
        backref=db.backref('offices', lazy=True)
    )


@dataclass
class OfficeListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = Office
    __query_fields__ = ('name', 'city', 'state', 'country')

    city: str = None
    state: str = None
    country: str = None

    department_id: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = list()

        filters.extend(super(OfficeListQueryParameters, self).get_filters())

        for field_name in ('city', 'state', 'country'):
            value = getattr(self, field_name, None)
            if value is not None:
                filters.append(get_string_filter(sa_fn.lower(getattr(Office, field_name)), value))

        if self.department_id:
            deparment = Department.get(auth_info, self.department_id, raise_if_not_found=True)
            filters.append(Office.departments.contains(deparment))

        return filters
