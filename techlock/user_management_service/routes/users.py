import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import (
    BadRequestException, ConflictException, NotFoundException,
    PageableQueryParametersSchema,
)
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)

from ..services import Auth0Idp, CognitoIdp
from ..models import (
    User, UserSchema, UserPageableSchema,
    USER_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('users', __name__, url_prefix='/users')


@blp.route('')
class Users(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        # self.idp = CognitoIdp()
        self.idp = Auth0Idp()

    @blp.arguments(PageableQueryParametersSchema, location='query')
    @blp.response(UserPageableSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, args):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = User.get_all(
            current_user,
            limit=args.get('limit', 50),
            start_key=args.get('start_key'),
            claims=claims,
        )

        logger.info('GET users', extra={
            'users': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(UserSchema)
    @blp.response(UserSchema, code=201)
    @access_required('create', 'users')
    def post(self, data):
        current_user = get_current_user()
        logger.info('Creating User', extra={'data': data})

        data['entity_id'] = data.get('email')
        User.validate(data)
        user = User.get(current_user, data['entity_id'])
        if user is not None:
            raise ConflictException('User with email = {} already exists.'.format(data['entity_id']))
        user = User(**data)
        user.save(current_user)
        logger.info('User created, adding to idp')

        self.idp.create_user(current_user, user)
        logger.info('User added to idp')

        return user


@blp.route('/<user_id>')
class UserById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = CognitoIdp()

    @blp.response(UserSchema)
    @access_required(
        'read', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def get(self, user_id):
        current_user = get_current_user()
        claims = get_request_claims()

        user = User.get(current_user, user_id)
        # If no access, return 404
        if user is None or not can_access(user, claims):
            raise NotFoundException('No user found for id = {}'.format(user_id))

        return user

    @blp.arguments(UserSchema)
    @blp.response(UserSchema)
    @access_required(
        'update', 'users',
        allowed_filter_fields=USER_CLAIM_SPEC.filter_fields
    )
    def put(self, data, user_id):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.debug('Updating User', extra={'data': data})

        User.validate(data, validate_required_fields=False)
        user = User.get(current_user, user_id)
        if user is None or not can_access(user, claims):
            raise NotFoundException('No user found for id = {}'.format(user_id))

        if user.email == data.get('email'):
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
    def delete(self, user_id):
        current_user = get_current_user()
        claims = get_request_claims()

        user = User.get(current_user, user_id)
        if user is None or not can_access(user, claims):
            raise NotFoundException('No user found for id = {}'.format(user_id))

        self.idp.delete_user(current_user, user)
        logger.info('Deleted user from userpool')

        user.delete(current_user)
        logger.info('Deleted user', extra={'user': user.asdict()})

        return
