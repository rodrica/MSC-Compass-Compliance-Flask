import logging
from typing import List, Union
from uuid import UUID

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint
from sqlalchemy import and_ as sql_and_  # diffentiate from operators.and_
from techlock.common.api import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from techlock.common.api.jwt_authorization import (
    Claim,
    access_required,
    can_access,
    get_request_claims,
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


def _get_items_from_id_list(current_user: AuthInfo, id_list: List[Union[str, UUID]], ormClass: BaseModel):
    items = list()
    if not id_list:
        return items

    for entity_id in id_list:
        items.append(ormClass.get(current_user, entity_id=entity_id, raise_if_not_found=True))

    return items


def _get_user(current_user: AuthInfo, user_id: str):
    claims = get_request_claims()

    user = User.get(current_user, user_id)
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

    @blp.arguments(UserListQueryParametersSchema, location='query')
    @blp.response(UserPageableSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: UserListQueryParameters):
        current_user = get_current_user()
        claims = get_request_claims()

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

    @blp.arguments(PostUserSchema)
    @blp.response(UserSchema, code=201)
    @access_required('create', 'users')
    def post(self, data: dict):
        current_user = get_current_user()
        logger.info('Creating User', extra={'data': data})

        # Get the password and remove it from the data. It is not part of the User object
        temporary_password = data.pop('temporary_password')
        # User.validate(data)
        user = User.get(current_user, data['email'])
        if user is not None:
            raise ConflictException('User with email = {} already exists.'.format(data['email']))

        ftp_username = data.get('ftp_username')
        if ftp_username == '':
            ftp_username = None
        if ftp_username and not _is_ftp_username_unique(current_user, ftp_username):
            # Validate that ftp_username is unique to the tenant
            raise ConflictException(f"ftp_username '{ftp_username}' already exists.")

        # Validate that items exist and get actual items
        roles = _get_items_from_id_list(current_user, data.get('role_ids'), Role)
        departments = _get_items_from_id_list(current_user, data.get('department_ids'), Department)
        offices = _get_items_from_id_list(current_user, data.get('office_ids'), Office)

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
        try:
            self.idp.create_user(current_user, user, password=temporary_password, idp_attributes=idp_attributes)
            self.idp.update_user_roles(current_user, user, user.roles)

            logger.info('User added to idp, storing internally')
            user.save(current_user)
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

    @blp.response(UserSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, user_id: str):
        current_user = get_current_user()
        user = _get_user(current_user, user_id)

        return user

    @blp.arguments(UpdateUserSchema)
    @blp.response(UserSchema)
    @access_required(
        'update', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def put(self, data: dict, user_id: str):
        current_user = get_current_user()
        logger.debug('Updating User', extra={'data': data})

        # User.validate(data, validate_required_fields=False)
        user = _get_user(current_user, user_id)

        if user.email != data.get('email'):
            raise BadRequestException('Email can not be changed.')

        # Validate that items exist and get actual items
        data['roles'] = _get_items_from_id_list(current_user, data.pop('role_ids', None), Role)
        data['departments'] = _get_items_from_id_list(current_user, data.pop('department_ids', None), Department)
        data['offices'] = _get_items_from_id_list(current_user, data.pop('office_ids', None), Office)

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

        user.save(current_user)

        self.idp.update_user_attributes(current_user, user, attributes_to_update)
        self.idp.update_user_roles(current_user, user, data['roles'])

        return user

    @blp.response(UserSchema, code=204)
    @access_required(
        'delete', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def delete(self, user_id: str):
        current_user = get_current_user()

        if current_user.user_id == user_id:
            return BadRequestException('Can not delete yourself.')

        user = _get_user(current_user, user_id)

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

    @blp.arguments(PostUserChangePasswordSchema)
    @blp.response()
    @access_required(
        'update', 'user_passwords',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def post(self, data: dict, user_id: str):
        current_user = get_current_user()
        user = _get_user(current_user, user_id)

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
