import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint
from uuid import UUID

from techlock.common.api import (
    BadRequestException, NotFoundException,
    Claim
)
from techlock.common.config import AuthInfo
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)

from ..models import (
    Role, RoleSchema, RolePageableSchema,
    RoleListQueryParameters, RoleListQueryParametersSchema,
    ROLE_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('roles', __name__, url_prefix='/roles')


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
class Roles(MethodView):

    @blp.arguments(RoleListQueryParametersSchema, location='query')
    @blp.response(RolePageableSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: RoleListQueryParameters):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = Role.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
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

        # Role.validate(data)
        role = Role(**data)
        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        role.save(current_user)

        return role


@blp.route('/<role_id>')
class RoleById(MethodView):

    def get_role(self, current_user: AuthInfo, role_id: str):
        claims = get_request_claims()

        role = Role.get(current_user, role_id)
        # If no access, return 404
        if role is None or not can_access(role, claims):
            raise NotFoundException('No role found for id = {}'.format(role_id))

        return role

    @blp.response(RoleSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, role_id):
        current_user = get_current_user()

        role = self.get_role(current_user, role_id)

        return role

    @blp.arguments(RoleSchema)
    @blp.response(RoleSchema)
    @access_required(
        'update', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, role_id):
        current_user = get_current_user()
        logger.debug('Updating Role', extra={'data': data})

        role = self.get_role(current_user, role_id)
        for k, v in data.items():
            if hasattr(role, k):
                setattr(role, k, v)
            else:
                raise BadRequestException('Role has no attribute: %s' % k)

        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        role.save(current_user)
        return role

    @blp.response(RoleSchema, code=204)
    @access_required(
        'delete', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def delete(self, role_id):
        current_user = get_current_user()

        role = self.get_role(current_user, role_id)

        role.delete(current_user)
        return role
