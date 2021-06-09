import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common import AuthInfo, ConfigManager
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema

from ..models import TENANT_CLAIM_SPEC as claim_spec
from ..models import (
    Tenant,
    TenantListQueryParameters,
    TenantListQueryParametersSchema,
    TenantPageableSchema,
    TenantSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('tenants', __name__, url_prefix='/tenants')


@blp.route('')
class Tenants(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=TenantListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=TenantPageableSchema)
    def get(self, query_params: TenantListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        pageable_resp = Tenant.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        logger.info('GET tenants', extra={'tenants': pageable_resp.asdict()})

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=TenantSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=TenantSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating Tenant', extra={'data': data})

        # Tenant.validate(data)
        tenant = Tenant(**data)
        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        tenant.save(current_user, claims=claims, commit=not dry_run)

        if not dry_run:
            # Create initial config item in DynamoDB
            cm = ConfigManager()
            cm.set(str(tenant.entity_id), 'name', tenant.name)

        return tenant


@blp.route('/<tenant_id>')
class TenantById(MethodView):

    def get_tenant(self, current_user: AuthInfo, claims: ClaimSet, tenant_id: str):
        tenant = Tenant.get(current_user, tenant_id, claims=claims, raise_if_not_found=True)

        return tenant

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=TenantSchema)
    def get(self, tenant_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting tenant', extra={'id': tenant_id})
        tenant = self.get_tenant(current_user, claims, tenant_id)

        return tenant

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=TenantSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=TenantSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, tenant_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating Tenant', extra={'data': data})

        tenant = self.get_tenant(current_user, claims.filter_by_action('read'), tenant_id)

        is_name_updated = 'name' in data and data['name'] != tenant.name
        for k, v in data.items():
            if hasattr(tenant, k):
                setattr(tenant, k, v)
            else:
                raise BadRequestException(f'Tenant has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        tenant.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)

        if is_name_updated and not dry_run:
            cm = ConfigManager()
            cm.set(str(tenant.entity_id), 'name', tenant.name)

        return tenant

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, tenant_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting tenant', extra={'id': tenant_id})
        tenant = self.get_tenant(current_user, claims.filter_by_action('read'), tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        tenant.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)
        return
