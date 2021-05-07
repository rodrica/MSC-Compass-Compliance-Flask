import logging
from typing import List, Union
from uuid import UUID

from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import and_ as sql_and_  # diffentiate from operators.and_
from techlock.common.api import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from techlock.common.api.auth import (
    Claim,
    access_required,
    can_access,
    get_current_user_with_claims,
)
from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.messaging.sns import Envelope
from techlock.common.messaging.sns import publish as publish_sns
from techlock.common.orm.sqlalchemy import BaseModel
from techlock.common.util.helper import suppress_with_log

from ..models import (
    USER_CLAIM_SPEC,
    Department,
    Office,
    PostUserChangePasswordSchema,
    PostUserSchema,
    Role,
    UpdateUserSchema,
    User,
    UserListQueryParameters,
    UserListQueryParametersSchema,
    UserPageableSchema,
    UserSchema,
)
from ..services import get_idp

logger = logging.getLogger(__name__)

blp = Blueprint('users', __name__, url_prefix='/users')

idp_attribute_keys = [
]


def _get_items_from_id_list(current_user: AuthInfo, claims: List[Claim], id_list: List[Union[str, UUID]], orm_class: BaseModel):
    items = list()
    if not id_list:
        return items

    for entity_id in id_list:
        items.append(orm_class.get(current_user, entity_id=entity_id, claims=claims, raise_if_not_found=True))

    return items


def _get_user(current_user: AuthInfo, claims: List[Claim], user_id: str):
    user = User.get(current_user, user_id, claims=claims)
    if user is None or (current_user.user_id != user_id and not can_access(user, claims)):
        raise NotFoundException('No user found for id = {}'.format(user_id))

    return user


def _is_ftp_username_unique(current_user: AuthInfo, ftp_username: str):
    ftp_user_count = User.query.filter(sql_and_(
        User.is_active.is_(True),
        User.ftp_username == ftp_username
    )).count()
    logger.debug(f'ftp_user_count: {ftp_user_count}')

    return ftp_user_count == 0


def set_claims_default_tenant(data: dict, default_tenant_id: UUID):
    claims_by_audience = data.get('claims_by_audience')
    if claims_by_audience is not None:
        for key, claims in claims_by_audience.items():
            new_claims = []
            for claim in claims:
                c = Claim.from_string(claim)
                if c.tenant_id == '':
                    c.tenant_id = default_tenant_id
                new_claims = new_claims + [str(c)]
            claims_by_audience[key] = new_claims
    return claims_by_audience


@blp.route('')
class Users(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @blp.arguments(schema=UserListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=UserPageableSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: UserListQueryParameters):
        current_user, claims = get_current_user_with_claims()
        if not claims:
            # if no claims, add one that allows the user to see himself
            claims = [Claim(True, current_user.tenant_id, '*', '*', 'users', id=current_user.user_id, filter_field=None, filter_value=None)]

        pageable_resp = User.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(current_user),
            claims=claims,
        )

        logger.info('GET users', extra={
            'users': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(schema=PostUserSchema)
    @blp.response(status_code=201, schema=UserSchema)
    @access_required('create', 'users')
    def post(self, data: dict):
        current_user, claims = get_current_user_with_claims()
        logger.info('Creating User', extra={'data': data})

        # Get the password and remove it from the data. It is not part of the User object
        temporary_password = data.pop('temporary_password')
        # User.validate(data)

        # Since users are to be unique across all tenants by email address, we must
        # get the full list of users, even ones from other tenants. Therefore we use
        # _unsecure_get() to get a list of users, even ones the requesting user does not
        # have authorization to see.
        user = User._unsecure_get(data['email'])
        if user is not None:
            raise ConflictException('User with email = {} already exists.'.format(data['email']))

        ftp_username = data.get('ftp_username')
        if ftp_username == '':
            ftp_username = None
        if ftp_username and not _is_ftp_username_unique(current_user, ftp_username):
            # Validate that ftp_username is unique to the tenant
            raise ConflictException(f"ftp_username '{ftp_username}' already exists.")

        # Validate that items exist and get actual items
        roles = _get_items_from_id_list(current_user, claims=claims, id_list=data.get('role_ids'), orm_class=Role)
        departments = _get_items_from_id_list(current_user, claims=claims, id_list=data.get('department_ids'), orm_class=Department)
        offices = _get_items_from_id_list(current_user, claims=claims, id_list=data.get('office_ids'), orm_class=Office)

        user = User(
            entity_id=data.get('email'),
            email=data.get('email'),
            name=data.get('name'),
            family_name=data.get('family_name'),
            ftp_username=ftp_username,
            description=data.get('description'),
            claims_by_audience=set_claims_default_tenant(data, current_user.tenant_id),
            tags=data.get('tags'),
            roles=roles,
            departments=departments,
            offices=offices,
        )

        logger.info('Adding user to idp')
        idp_attributes = {k: v for k, v in data.items() if k in idp_attribute_keys}

        self.idp.create_user(current_user, user, password=temporary_password, idp_attributes=idp_attributes)

        try:
            self.idp.update_user_roles(current_user, user, user.roles)

            logger.info('User added to idp, storing internally')
            user.save(current_user, claims=claims)
            logger.info('User created')
        except Exception:
            # Clean up silently. We expect part of this to fail, because if everything was created properly, we wouldn't be here.
            # Bit of a lazy approach :)
            with suppress_with_log(logger, Exception, log_level=logging.DEBUG):
                self.idp.delete_user(current_user, user)

            with suppress_with_log(logger, Exception, log_level=logging.DEBUG):
                user = _get_user(current_user, data['email'])
                user.delete(current_user)

            raise

        return user


@blp.route('/<user_id>')
class UserById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @blp.response(status_code=200, schema=UserSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, user_id: str):
        current_user, claims = get_current_user_with_claims()
        user = _get_user(current_user, claims, user_id)

        return user

    @blp.arguments(schema=UpdateUserSchema)
    @blp.response(status_code=200, schema=UserSchema)
    @access_required(
        'update', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def put(self, data: dict, user_id: str):
        current_user, claims = get_current_user_with_claims()
        logger.debug('Updating User', extra={'data': data})

        # User.validate(data, validate_required_fields=False)
        user = _get_user(current_user, claims, user_id)

        if user.email != data.get('email'):
            raise BadRequestException('Email can not be changed.')

        # Validate that items exist and get actual items
        data['roles'] = _get_items_from_id_list(current_user, claims=claims, id_list=data.pop('role_ids', None), orm_class=Role)
        data['departments'] = _get_items_from_id_list(current_user, claims=claims, id_list=data.pop('department_ids', None), orm_class=Department)
        data['offices'] = _get_items_from_id_list(current_user, claims=claims, id_list=data.pop('office_ids', None), orm_class=Office)

        ftp_username = data.get('ftp_username')
        if ftp_username == '':
            ftp_username = None
        if ftp_username and ftp_username != user.ftp_username and not _is_ftp_username_unique(current_user, ftp_username):
            # Validate that ftp_username is unique to the tenant
            raise ConflictException(f"ftp_username '{ftp_username}' already exists.")

        attributes_to_update = dict()
        for k, v in data.items():
            if k in idp_attribute_keys:
                attributes_to_update[k] = v
            elif hasattr(user, k):
                setattr(user, k, v)
                if k in ('name', 'family_name'):
                    attributes_to_update[k] = v
            else:
                raise BadRequestException('User has no attribute: %s' % k)

        user.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        user.save(current_user, claims=claims)

        self.idp.update_user_attributes(current_user, user, attributes_to_update)
        self.idp.update_user_roles(current_user, user, data['roles'])

        return user

    @blp.response(status_code=204, schema=UserSchema)
    @access_required(
        'delete', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def delete(self, user_id: str):
        current_user, claims = get_current_user_with_claims()

        if current_user.user_id == user_id:
            return BadRequestException('Can not delete yourself.')

        user = _get_user(current_user, claims, user_id)

        self.idp.delete_user(current_user, user)
        logger.info('Deleted user from userpool')

        user.delete(current_user)
        logger.info('Deleted user', extra={'user': user.entity_id})

        return


@blp.route('/<user_id>/change_password')
class UserChangePassword(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @blp.arguments(schema=PostUserChangePasswordSchema)
    @blp.response(status_code=200)
    @access_required(
        'update', 'user_passwords',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def post(self, data: dict, user_id: str):
        current_user, claims = get_current_user_with_claims()
        user = _get_user(current_user, claims, user_id)

        self.idp.change_password(current_user, user, data.get('new_password'))

        cm = ConfigManager()
        # Password was successfully changed, log any errors that occur in the post processing
        # But don't raise it, we need to prevent the request itself from returning an error code.
        with suppress_with_log(logger):
            publish_sns(Envelope(
                topic_arn=cm.get('sns.topics.UserNotification'),
                subject='Password Changed',
                message={
                    'user_id': user_id,
                    'changed_by': current_user.user_id
                },
                tenant_id=current_user.tenant_id,
                source='user-management-service',
                severity='INFO',
            ))
