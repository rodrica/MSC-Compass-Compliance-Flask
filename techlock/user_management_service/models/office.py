import marshmallow as ma
import marshmallow.fields as mf
from boto3.dynamodb.conditions import Attr
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Dict, List

from techlock.common.api import (
    ClaimSpec,
    PageableResponse, PageableResponseBaseSchema,
    PageableQueryParameters, PageableQueryParametersSchema,
)

from techlock.common.config import AuthInfo
from techlock.common.orm.dynamodb import (
    NO_DEFAULT,
    PersistedObject,
    PersistedObjectSchema,
)

from .department import Department

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


class OfficeSchema(PersistedObjectSchema):
    name = mf.String()
    description = mf.String(allow_none=True)

    street1 = mf.String(allow_none=True)
    street2 = mf.String(allow_none=True)
    street3 = mf.String(allow_none=True)
    city = mf.String(allow_none=True)
    state = mf.String(allow_none=True)
    country = mf.String(allow_none=True)
    postal_code = mf.String(allow_none=True)
    latitude = mf.Decimal(allow_none=True)
    longitude = mf.Decimal(allow_none=True)

    department_ids = mf.List(mf.String(), allow_none=True)

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class OfficeListQueryParametersSchema(PageableQueryParametersSchema):
    name = mf.String(allow_none=True, description='Used to filter offices by name prefix.')
    city = mf.String(allow_none=True, description='Used to filter offices by city prefix.')
    state = mf.String(allow_none=True, description='Used to filter offices by state prefix.')
    country = mf.String(allow_none=True, description='Used to filter offices by country prefix.')

    department_ids = mf.String(allow_none=True, description='Used to filter offices by department_ids. Comma delimited list of exact ids.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return OfficeListQueryParameters(**data)


class OfficePageableSchema(PageableResponseBaseSchema):
    items = mf.Nested(OfficeSchema, many=True, dump_only=True)


@dataclass
class Office(PersistedObject):
    table: ClassVar[str] = 'offices'

    name: str = NO_DEFAULT
    description: str = None
    street1: str = None
    street2: str = None
    street3: str = None
    city: str = None
    state: str = None
    country: str = None
    postal_code: str = None
    latitude: Decimal = None
    longitude: Decimal = None

    department_ids: List[str] = None

    tags: Dict[str, str] = None

    def __post_init__(self):
        super(Office, self).__post_init__()
        if self.latitude and not isinstance(self.latitude, Decimal):
            self.latitude = Decimal("{}".format(self.latitude))
        if self.longitude and not isinstance(self.longitude, Decimal):
            self.longitude = Decimal("{}".format(self.longitude))

    def get_departments(self, auth_info: AuthInfo):
        '''Lazy load Departments'''
        data = PageableResponse()
        if self.department_ids:
            data = Department.get_all(auth_info, ids=self.department_ids)
        return data

    @classmethod
    def get_by_department_id(cls, auth_info: AuthInfo, department_id):
        attrs = [
            Attr('department_ids').contains(department_id)
        ]

        data = Office.get_all(auth_info, additional_attrs=attrs)
        return data


@dataclass
class OfficeListQueryParameters(PageableQueryParameters):
    name: str = None
    city: str = None
    state: str = None
    country: str = None

    department_ids: str = None

    def get_filters(self):
        ddb_attrs = list()

        for attr in ('name', 'city', 'state', 'country'):
            if getattr(self, attr, None) is not None:
                ddb_attrs.append(Attr(attr).begins_with(getattr(self, attr)))

        if self.department_ids is not None:
            values = self.department_ids.split(',')
            for v in values:
                ddb_attrs.append(Attr(attr).contains(v))

        return ddb_attrs
