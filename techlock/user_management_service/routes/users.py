import json
import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import (
    BadRequestException, ConflictException, NotFoundException,
)
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)
from techlock.common.config import AuthInfo
from techlock.common.messaging import UserNotification, Level, publish_sns

from ..services import get_idp
from ..models import (
    User, UserSchema, UserPageableSchema,
    Department, Office, Role,
    UserListQueryParameters, UserListQueryParametersSchema,
    PostUserSchema,
    UpdateUserSchema,
    PostUserChangePasswordSchema,
    USER_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('users', __name__, url_prefix='/users')


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
            raise ConflictException('User with email = {} already exists.'.format(data['entity_id']))

        # Validate that items exist and get actual items
        roles = list()
        for entity_id in data.get('role_ids', list()):
            roles.append(Role.get(current_user, entity_id=entity_id, raise_if_not_found=True))
        departments = list()
        for entity_id in data.get('department_ids', list()):
            departments.append(Department.get(current_user, entity_id=entity_id, raise_if_not_found=True))
        offices = list()
        for entity_id in data.get('office_ids', list()):
            offices.append(Office.get(current_user, entity_id=entity_id, raise_if_not_found=True))

        user = User(
            entity_id=data.get('email'),
            email=data.get('email'),
            name=data.get('name'),
            family_name=data.get('family_name'),
            claims_by_audience=data.get('claims_by_audience'),
            tags=data.get('tags'),
            roles=roles,
            departments=departments,
            offices=offices,
        )

        logger.info('Adding user to idp')
        self.idp.create_user(current_user, user, password=temporary_password)
        logger.info('User added to idp, storing internally')

        user.save(current_user)
        logger.info('User created')

        return user


@blp.route('/<user_id>')
class UserById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    def get_user(self, current_user: AuthInfo, user_id: str):
        claims = get_request_claims()

        user = User.get(current_user, user_id)
        if user is None or not can_access(user, claims):
            raise NotFoundException('No user found for id = {}'.format(user_id))

        return user

    @blp.response(UserSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, user_id: str):
        current_user = get_current_user()
        user = self.get_user(current_user, user_id)

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
        user = self.get_user(current_user, user_id)

        if user.email != data.get('email'):
            raise BadRequestException('Email can not be changed.')

        attributes_to_update = dict()
        for k, v in data.items():
            if hasattr(user, k):
                setattr(user, k, v)
                if k in ('name', 'family_name'):
                    attributes_to_update[k] = v
            else:
                raise BadRequestException('User has no attribute: %s' % k)
        user.save(current_user)
        self.idp.update_user_attributes(current_user, user, attributes_to_update)

        return user

    @blp.response(UserSchema, code=204)
    @access_required(
        'delete', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def delete(self, user_id: str):
        current_user = get_current_user()
        user = self.get_user(current_user, user_id)

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
    def post(self, data: dict, user_id: str):
        current_user = get_current_user()
        user = self.get_user(current_user, user_id)

        self.idp.change_password(current_user, user, data.get('new_password'))

        publish_sns(UserNotification(
            subject='Password Changed',
            message=json.dumps({
                'changed_by': current_user.user_id
            }),
            created_by='user-management-service',
            tenant_id=current_user.tenant_id,
            level=Level.warning,
        ))
