import marshmallow as ma
import marshmallow.fields as mf
from boto3.dynamodb.conditions import Attr
from dataclasses import dataclass
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
from .office import Office

__all__ = [
    'User',
    'UserSchema',
    'UserPageableSchema',
    'UserListQueryParametersSchema',
    'PostUserSchema',
    'PostUserChangePasswordSchema',
    'USER_CLAIM_SPEC',
]


USER_CLAIM_SPEC = ClaimSpec(
    actions=[
        'create',
        'read',
        'update',
        'delete'
    ],
    resource_name='users',
    filter_fields=[
        'email',

        # Really want these, but not sure how to handle it yet.
        # Atm only filtering on actual fields is supported.
        # Might need to implement some sort of mapping.
        # Maybe something like:
        #  'role': {'field': 'role_ids', 'type': 'list'}
        # Or tie it to the Schema:
        #  'role': 'role_ids' (and figure out it's a list via reflection)

        # 'office',
        # 'department',
        # 'role',
    ]
)


class UserSchema(PersistedObjectSchema):
    email = mf.String(required=True)
    name = mf.String(required=True)
    family_name = mf.String()

    role_ids = mf.List(mf.String(), allow_none=True)
    department_ids = mf.List(mf.String(), allow_none=True)
    office_ids = mf.List(mf.String(), allow_none=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String()),
        allow_none=True
    )

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)


class PostUserSchema(UserSchema):
    temporary_password = mf.String(required=True)


class PostUserChangePasswordSchema(ma.Schema):
    new_password = mf.String(required=True)


class UserListQueryParametersSchema(PageableQueryParametersSchema):
    email = mf.String(allow_none=True, description='Used to filter users by email prefix.')
    name = mf.String(allow_none=True, description='Used to filter users by name prefix.')
    family_name = mf.String(allow_none=True, description='Used to filter users by family_name prefix.')

    role_ids = mf.String(allow_none=True, description='Used to filter users by role_ids. Comma delimited list of exact ids.')
    department_ids = mf.String(allow_none=True, description='Used to filter users by department_ids. Comma delimited list of exact ids.')
    office_ids = mf.String(allow_none=True, description='Used to filter users by office_ids. Comma delimited list of exact ids.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return UserListQueryParameters(**data)


class UserPageableSchema(PageableResponseBaseSchema):
    items = mf.Nested(UserSchema, many=True, dump_only=True)


@dataclass
class User(PersistedObject):
    table: ClassVar[str] = 'users'
    # We'll be using the Cognito User Id as entity id.
    is_entity_id_required: ClassVar[bool] = True

    email: str = NO_DEFAULT
    name: str = NO_DEFAULT
    family_name: str = NO_DEFAULT

    role_ids: List[str] = None
    department_ids: List[str] = None
    office_ids: List[str] = None
    claims_by_audience: Dict[str, List[str]] = None

    tags: Dict[str, str] = None

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

        data = User.get_all(auth_info, additional_attrs=attrs)
        return data

    def get_offices(self, auth_info: AuthInfo):
        '''Lazy load Offices'''
        data = PageableResponse()
        if self.office_ids:
            data = Office.get_all(auth_info, ids=self.office_ids)
        return data

    @classmethod
    def get_by_office_id(cls, auth_info: AuthInfo, office_id):
        attrs = [
            Attr('office_ids').contains(office_id)
        ]

        data = User.get_all(auth_info, additional_attrs=attrs)
        return data


@dataclass
class UserListQueryParameters(PageableQueryParameters):
    email: str = None
    name: str = None
    family_name: str = None

    role_ids: str = None
    department_ids: str = None
    office_ids: str = None

    def get_filters(self):
        ddb_attrs = list()

        for attr in ('email', 'name', 'family_name'):
            if getattr(self, attr, None) is not None:
                ddb_attrs.append(Attr(attr).begins_with(getattr(self, attr)))

        for attr in ('role_ids', 'department_ids', 'office_ids'):
            if getattr(self, attr, None) is not None:
                values = getattr(self, attr).split(',')
                for v in values:
                    ddb_attrs.append(Attr(attr).contains(v))

        return ddb_attrs
