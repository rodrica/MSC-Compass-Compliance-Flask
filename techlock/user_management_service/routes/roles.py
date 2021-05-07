import logging
from typing import List
from uuid import UUID

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException, Claim, NotFoundException
from techlock.common.api.auth import (
    access_required,
    get_current_user_with_claims,
)
from techlock.common.config import AuthInfo

from ..models import (
    ROLE_CLAIM_SPEC,
    Role,
    RoleListQueryParameters,
    RoleListQueryParametersSchema,
    RolePageableSchema,
    RoleSchema,
)
from ..services import get_idp

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

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @blp.arguments(schema=RoleListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=RolePageableSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: RoleListQueryParameters):
        current_user, claims = get_current_user_with_claims()

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

    @blp.arguments(schema=RoleSchema)
    @blp.response(status_code=201, schema=RoleSchema)
    @access_required('create', 'roles')
    def post(self, data):
        current_user, claims = get_current_user_with_claims()
        logger.info('Creating Role', extra={'data': data})

        # Role.validate(data)
        role = Role(**data)
        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        role.save(current_user, claims=claims)

        self.idp.update_or_create_role(current_user, role)

        return role


@blp.route('/<role_id>')
class RoleById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    def get_role(self, current_user: AuthInfo, claims: List[Claim], role_id: str):
        role = Role.get(current_user, role_id, claims=claims, raise_if_not_found=True)

        return role

    @blp.response(status_code=200, schema=RoleSchema)
    @access_required(
        'read', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def get(self, role_id):
        current_user, claims = get_current_user_with_claims()

        role = self.get_role(current_user, claims, role_id)

        return role

    @blp.arguments(schema=RoleSchema)
    @blp.response(status_code=200, schema=RoleSchema)
    @access_required(
        'update', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, role_id):
        current_user, claims = get_current_user_with_claims()
        logger.debug('Updating Role', extra={'data': data})

        role = self.get_role(current_user, claims, role_id)

        for k, v in data.items():
            if hasattr(role, k):
                setattr(role, k, v)
            else:
                raise BadRequestException('Role has no attribute: %s' % k)

        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        role.save(current_user, claims=claims)
        self.idp.update_or_create_role(current_user, role)

        return role

    @blp.response(status_code=204, schema=RoleSchema)
    @access_required(
        'delete', 'roles',
        allowed_filter_fields=ROLE_CLAIM_SPEC.filter_fields
    )
    def delete(self, role_id):
        current_user, claims = get_current_user_with_claims()
        role = self.get_role(current_user, claims, role_id)

        try:
            self.idp.delete_role(current_user, role)
        except NotFoundException:
            logger.warning('Role does not exist in IDP, skipping IDP deletion...', extra={'role_idp_name': role.idp_name})

        role.delete(current_user)
        return role
