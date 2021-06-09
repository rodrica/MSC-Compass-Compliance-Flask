import logging
from dataclasses import dataclass

import marshmallow as ma
import marshmallow.fields as mf
import marshmallow.validate as mv
from sqlalchemy import func as sa_fn
from sqlalchemy.dialects.postgresql import JSONB, UUID
from techlock.common.api import (
    BaseOffsetListQueryParams,
    BaseOffsetListQueryParamsSchema,
    Claim,
    ClaimSpec,
    NotFoundException,
    OffsetPageableResponseBaseSchema,
)
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import BaseModel, BaseModelSchema, db, get_string_filter

from ..services import get_idp
from .department import Department, DepartmentSchema
from .office import Office, OfficeSchema
from .role import Role, RoleSchema

logger = logging.getLogger(__name__)

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
        'delete',
    ],
    resource_name='users',
    filter_fields=[
        'created_by',
        'email',

        # Really want these, but not sure how to handle it yet.
        # Atm only filtering on actual fields is supported.
        # Might need to implement some sort of mapping.
        # Maybe something like:
        #  'role': {'field': 'role_ids', 'type': 'list'}
        # Or tie it to the Schema:
        #  'role': 'role_ids' (and figure out it's a list via reflection)

        # I.e.: You can only see users in a particular office or department
        # For example, a department head can only view it's sub-ordinates

        # 'office',
        # 'department',
        # 'role',
    ],
    # There will be no system users, so no default actions.
    default_actions=[],
)


class Email(mf.Email):
    '''
        Convert Email address to lowercase.
    '''
    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        return value.lower()

    def _deserialize(self, value, attr, obj, **kwargs):
        value = super()._deserialize(value, attr, obj, **kwargs)
        return value.lower()


class UserSchema(BaseModelSchema):
    email = Email(required=True)
    family_name = mf.String()
    ftp_username = mf.String(validate=mv.Regexp(r'^[a-zA-Z0-9_][a-zA-Z0-9_-]{2,31}$', error='String does not match expected pattern: {regex}.'), allow_none=True)
    login_info = mf.Dict(mf.String(), mf.String(), dump_only=True)

    # DEPRECATED, need to remove this since it's problematic with permissions
    roles = mf.Nested(RoleSchema, allow_none=True, many=True)
    departments = mf.Nested(DepartmentSchema, allow_none=True, many=True)
    offices = mf.Nested(OfficeSchema, allow_none=True, many=True)

    role_ids = mf.List(mf.UUID(), required=False, allow_none=True)
    department_ids = mf.List(mf.UUID(), required=False, allow_none=True)
    office_ids = mf.List(mf.UUID(), required=False, allow_none=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String(validate=Claim.validate_claim_string)),
        allow_none=True,
    )

    @ma.pre_dump
    def pre_dump(self, data: 'User', **kwargs):
        data.role_ids = []
        data.department_ids = []
        data.office_ids = []

        if data.roles:
            data.role_ids = [x.entity_id for x in data.roles]

        if data.departments:
            data.department_ids = [x.entity_id for x in data.departments]

        if data.offices:
            data.office_ids = [x.entity_id for x in data.offices]

        return data


class UpdateUserSchema(ma.Schema):
    email = Email(required=True)
    name = mf.String(required=True)
    family_name = mf.String(required=True)
    description = mf.String()
    ftp_username = mf.String(validate=mv.Regexp(r'^$|^[a-zA-Z0-9_][a-zA-Z0-9_-]{2,31}$', error='String does not match expected pattern: {regex}.'), allow_none=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String(validate=Claim.validate_claim_string)),
        allow_none=True,
    )

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)

    role_ids = mf.List(mf.UUID(), required=False, allow_none=True)
    department_ids = mf.List(mf.UUID(), required=False, allow_none=True)
    office_ids = mf.List(mf.UUID(), required=False, allow_none=True)


class PostUserSchema(UpdateUserSchema):
    temporary_password = mf.String(required=True)


class PostUserChangePasswordSchema(ma.Schema):
    new_password = mf.String(required=True)


class UserListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    email = mf.String(allow_none=True, description='Used to filter users by email prefix.')
    family_name = mf.String(allow_none=True, description='Used to filter users by family_name prefix.')
    ftp_username = mf.String(allow_none=True, description='Used to filter users by ftp_username prefix.')

    role_ids = mf.UUID(allow_none=True, description='Used to filter users by role_ids. Comma delimited list of exact ids.')
    department_ids = mf.UUID(allow_none=True, description='Used to filter users by department_ids. Comma delimited list of exact ids.')
    office_ids = mf.UUID(allow_none=True, description='Used to filter users by office_ids. Comma delimited list of exact ids.')

    @ma.post_load
    def make_object(self, data, **kwargs):
        return UserListQueryParameters(**data)


class UserPageableSchema(OffsetPageableResponseBaseSchema):
    items = mf.Nested(UserSchema, many=True, dump_only=True)


users_to_roles = db.Table(
    'users_to_roles',
    db.Column('user_id', db.String, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', UUID(as_uuid=True), db.ForeignKey('roles.id'), primary_key=True),
)
users_to_departments = db.Table(
    'users_to_departments',
    db.Column('user_id', db.String, db.ForeignKey('users.id'), primary_key=True),
    db.Column('department_id', UUID(as_uuid=True), db.ForeignKey('departments.id'), primary_key=True),
)
users_to_offices = db.Table(
    'users_to_offices',
    db.Column('user_id', db.String, db.ForeignKey('users.id'), primary_key=True),
    db.Column('office_id', UUID(as_uuid=True), db.ForeignKey('offices.id'), primary_key=True),
)


class User(BaseModel):
    __tablename__ = 'users'

    entity_id = db.Column('id', db.String, primary_key=True)
    email = db.Column(db.String, unique=False, nullable=False)
    family_name = db.Column(db.String, unique=False, nullable=False)
    ftp_username = db.Column(db.String, unique=False, nullable=True)

    roles = db.relationship(
        'Role',
        secondary=users_to_roles,
        lazy='subquery',
        backref=db.backref('users', lazy=True),
    )
    departments = db.relationship(
        'Department',
        secondary=users_to_departments,
        lazy='subquery',
        backref=db.backref('users', lazy=True),
    )
    offices = db.relationship(
        'Office',
        secondary=users_to_offices,
        lazy='subquery',
        backref=db.backref('users', lazy=True),
    )

    claims_by_audience = db.Column(JSONB, nullable=True)

    _idp_attrs = None

    def _fetch_idp_attrs(self):
        idp = get_idp()
        self._idp_attrs = idp.get_user_attributes(self)

    @property
    def login_info(self):
        try:
            if self._idp_attrs is None:
                self._fetch_idp_attrs()
        except NotFoundException:
            # Exception is logged in the IDP code
            return None

        return (self._idp_attrs or {}).get('login_info')


@dataclass
class UserListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = User
    __query_fields__ = ('name', 'family_name', 'email')

    email: str = None
    family_name: str = None
    ftp_username: str = None

    role_id: str = None
    department_id: str = None
    office_id: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = []

        filters.extend(super(UserListQueryParameters, self).get_filters())

        for field_name in ('email', 'family_name'):
            value = getattr(self, field_name, None)
            if value is not None:
                filters.append(get_string_filter(sa_fn.lower(getattr(User, field_name)), value))

        if self.role_id:
            role = Role.get(auth_info, self.role_id, raise_if_not_found=True)
            filters.append(User.roles.contains(role))

        if self.department_id:
            department = Department.get(auth_info, self.department_id, raise_if_not_found=True)
            filters.append(User.departments.contains(department))

        if self.office_id:
            office = Office.get(auth_info, self.office_id, raise_if_not_found=True)
            filters.append(User.offices.contains(office))

        return filters
