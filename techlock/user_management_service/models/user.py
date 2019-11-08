import marshmallow as ma
import marshmallow.fields as mf
from dataclasses import dataclass
from sqlalchemy import func as sa_fn
from sqlalchemy.dialects.postgresql import JSONB, UUID

from techlock.common.api import (
    Claim, ClaimSpec,
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
from .office import Office, OfficeSchema
from .role import Role, RoleSchema

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


class UserSchema(BaseModelSchema):
    email = mf.Email(required=True)
    family_name = mf.String()

    roles = mf.Nested(RoleSchema, allow_none=True, many=True)
    departments = mf.Nested(DepartmentSchema, allow_none=True, many=True)
    offices = mf.Nested(OfficeSchema, allow_none=True, many=True)

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String(validate=Claim.validate_claim_string)),
        allow_none=True
    )


class UpdateUserSchema(ma.Schema):
    email = mf.Email(required=True)
    name = mf.String(required=True)
    family_name = mf.String()
    description = mf.String()

    claims_by_audience = mf.Dict(
        keys=mf.String(),
        values=mf.List(mf.String(validate=Claim.validate_claim_string)),
        allow_none=True
    )

    tags = mf.Dict(keys=mf.String(), values=mf.String(), allow_none=True)

    role_ids = mf.List(mf.UUID(), required=False)
    department_ids = mf.List(mf.UUID(), required=False)
    office_ids = mf.List(mf.UUID(), required=False)


class PostUserSchema(UpdateUserSchema):
    temporary_password = mf.String(required=True)


class PostUserChangePasswordSchema(ma.Schema):
    new_password = mf.String(required=True)


class UserListQueryParametersSchema(BaseOffsetListQueryParamsSchema):
    email = mf.String(allow_none=True, description='Used to filter users by email prefix.')
    family_name = mf.String(allow_none=True, description='Used to filter users by family_name prefix.')

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
    db.Column('role_id', UUID(as_uuid=True), db.ForeignKey('roles.id'), primary_key=True)
)
users_to_departments = db.Table(
    'users_to_departments',
    db.Column('user_id', db.String, db.ForeignKey('users.id'), primary_key=True),
    db.Column('department_id', UUID(as_uuid=True), db.ForeignKey('departments.id'), primary_key=True)
)
users_to_offices = db.Table(
    'users_to_offices',
    db.Column('user_id', db.String, db.ForeignKey('users.id'), primary_key=True),
    db.Column('office_id', UUID(as_uuid=True), db.ForeignKey('offices.id'), primary_key=True)
)


class User(BaseModel):
    __tablename__ = 'users'

    entity_id = db.Column('id', db.String, primary_key=True)
    email = db.Column(db.String, unique=False, nullable=False)
    family_name = db.Column(db.String, unique=False, nullable=False)

    roles = db.relationship(
        'Role',
        secondary=users_to_roles,
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )
    departments = db.relationship(
        'Department',
        secondary=users_to_departments,
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )
    offices = db.relationship(
        'Office',
        secondary=users_to_offices,
        lazy='subquery',
        backref=db.backref('users', lazy=True)
    )

    claims_by_audience = db.Column(JSONB, nullable=True)


@dataclass
class UserListQueryParameters(BaseOffsetListQueryParams):
    __db_model__ = User
    __query_fields__ = ('name', 'family_name', 'email')

    email: str = None
    family_name: str = None

    role_id: str = None
    department_id: str = None
    office_id: str = None

    def get_filters(self, auth_info: AuthInfo):
        filters = list()

        filters.extend(super(UserListQueryParameters, self).get_filters())

        for field_name in ('email', 'family_name'):
            value = getattr(self, field_name, None)
            if value is not None:
                filters.append(get_string_filter(sa_fn.lower(getattr(User, field_name)), value))

        if self.role_id:
            role = Role.get(auth_info, self.role_id, raise_if_not_found=True)
            filters.append(User.roles.contains(role))

        if self.department_id:
            deparment = Department.get(auth_info, self.department_id, raise_if_not_found=True)
            filters.append(User.deparments.contains(deparment))

        if self.office_id:
            office = Office.get(auth_info, self.office_id, raise_if_not_found=True)
            filters.append(User.offices.contains(office))

        return filters
