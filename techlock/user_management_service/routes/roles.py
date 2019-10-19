import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import (
    BadRequestException, NotFoundException,
    PageableQueryParametersSchema,
)
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)

from ..models import (
    Role, RoleSchema, RolePageableSchema,
    ROLE_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('roles', __name__, url_prefix='/roles')


@blp.route('')
class Roles(MethodView):

    @blp.arguments(PageableQueryParametersSchema, location='query')
    @blp.response(RolePageableSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, args):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = Role.get_all(
            current_user,
            limit=args.get('limit', 50),
            start_key=args.get('start_key'),
            claims=claims,
        )

        logger.info('GET roles', extra={
            'roles': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(RoleSchema)
    @blp.response(RoleSchema, code=201)
    @access_required('create', 'roles')
    def post(self, data):
        current_user = get_current_user()
        logger.info('Creating Role', extra={'data': data})

        Role.validate(data)
        role = Role(**data)
        role.save(current_user)

        return role


@blp.route('/<role_id>')
class RoleById(MethodView):

    @blp.response(RoleSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, role_id):
        current_user = get_current_user()
        claims = get_request_claims()

        role = Role.get(current_user, role_id)
        # If no access, return 404
        if role is None or not can_access(role, claims):
            raise NotFoundException('No role found for id = {}'.format(role_id))

        return role

    @blp.arguments(RoleSchema)
    @blp.response(RoleSchema)
    @access_required(
        'update', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, role_id):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.debug('Updating Role', extra={'data': data})

        Role.validate(data, validate_required_fields=False)
        role = Role.get(current_user, role_id)
        if role is None or not can_access(role, claims):
            raise NotFoundException('No role found for id = {}'.format(role_id))

        for k, v in data.items():
            if hasattr(role, k):
                setattr(role, k, v)
            else:
                raise BadRequestException('Role has no attribute: %s' % k)
        role.save(current_user)
        return role

    @blp.response(RoleSchema, code=204)
    @access_required(
        'delete', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def delete(self, role_id):
        current_user = get_current_user()
        claims = get_request_claims()

        role = Role.get(current_user, role_id)
        if role is None or not can_access(role, claims):
            raise NotFoundException('No role found for id = {}'.format(role_id))

        role.delete(current_user)
        return role
