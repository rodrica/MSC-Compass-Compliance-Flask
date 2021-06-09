import logging
from dataclasses import asdict
from typing import Any, Dict
from uuid import UUID

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException, Claim, NotFoundException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import ROLE_CLAIM_SPEC as claim_spec
from ..models import (
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
                    c = Claim(**{**asdict(c), 'tenant_id': default_tenant_id})
                new_claims = new_claims + [str(c)]
            claims_by_audience[key] = new_claims
    return claims_by_audience


@blp.route('')
class Roles(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=RoleListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=RolePageableSchema)
    def get(self, query_params: RoleListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        pageable_resp = Role.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        logger.info('GET roles', extra={'roles': pageable_resp.asdict()})

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=RoleSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=RoleSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating role', extra={'data': data})

        role = Role(**data)
        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        role.save(current_user, claims=claims, commit=not dry_run)

        if not dry_run:
            self.idp.update_or_create_role(current_user, role)

        return role


@blp.route('/<role_id>')
class RoleById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    def get_role(self, current_user: AuthInfo, claims: ClaimSet, role_id: str):
        role = Role.get(current_user, role_id, claims=claims, raise_if_not_found=True)

        return role

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=RoleSchema)
    def get(self, role_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting role', extra={'id': role_id})
        role = self.get_role(current_user, claims, role_id)

        return role

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=RoleSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=RoleSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, role_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating role', extra={'data': data})

        role = self.get_role(current_user, claims.filter_by_action('read'), role_id)

        for k, v in data.items():
            if hasattr(role, k):
                setattr(role, k, v)
            else:
                raise BadRequestException(f'Role has no attribute: {k}')

        role.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        role.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)
        if not dry_run:
            self.idp.update_or_create_role(current_user, role)

        return role

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, role_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting role', extra={'id': role_id})

        role = self.get_role(current_user, claims.filter_by_action('read'), role_id)

        if not dry_run:
            try:
                self.idp.delete_role(current_user, role)
            except NotFoundException:
                logger.warning('Role does not exist in IDP, skipping IDP deletion...', extra={'role_idp_name': role.idp_name})

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        role.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)

        return
