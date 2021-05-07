import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint
from techlock.common import AuthInfo, ConfigManager
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required, get_request_claims

from ..models import (
    TENANT_CLAIM_SPEC,
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

    @blp.arguments(schema=TenantListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=TenantPageableSchema)
    @access_required(
        'read', 'tenants',
        allowed_filter_fields=TENANT_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: TenantListQueryParameters):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = Tenant.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        logger.info('GET tenants', extra={
            'tenants': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(schema=TenantSchema)
    @blp.response(status_code=201, schema=TenantSchema)
    @access_required('create', 'tenants')
    def post(self, data):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.info('Creating Tenant', extra={'data': data})

        # Tenant.validate(data)
        tenant = Tenant(**data)
        tenant.save(current_user, claims=claims)

        # Create initial config item in DynamoDB
        cm = ConfigManager()
        cm.set(str(tenant.entity_id), 'name', tenant.name)

        return tenant


@blp.route('/<tenant_id>')
class TenantById(MethodView):

    def get_tenant(self, current_user: AuthInfo, tenant_id: str):
        claims = get_request_claims()

        tenant = Tenant.get(current_user, tenant_id, claims=claims)

        return tenant

    @blp.response(status_code=200, schema=TenantSchema)
    @access_required(
        'read', 'tenants',
        allowed_filter_fields=TENANT_CLAIM_SPEC.filter_fields
    )
    def get(self, tenant_id):
        current_user = get_current_user()

        tenant = self.get_tenant(current_user, tenant_id)

        return tenant

    @blp.arguments(schema=TenantSchema)
    @blp.response(status_code=200, schema=TenantSchema)
    @access_required(
        'update', 'tenants',
        allowed_filter_fields=TENANT_CLAIM_SPEC.filter_fields
    )
    def put(self, data, tenant_id):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.debug('Updating Tenant', extra={'data': data})

        tenant = self.get_tenant(current_user, tenant_id)

        is_name_updated = 'name' in data and data['name'] != tenant.name
        for k, v in data.items():
            if hasattr(tenant, k):
                setattr(tenant, k, v)
            else:
                raise BadRequestException('Tenant has no attribute: %s' % k)
        tenant.save(current_user, claims=claims)

        if is_name_updated:
            cm = ConfigManager()
            cm.set(str(tenant.entity_id), 'name', tenant.name)

        return tenant

    @blp.response(status_code=204, schema=TenantSchema)
    @access_required(
        'delete', 'tenants',
        allowed_filter_fields=TENANT_CLAIM_SPEC.filter_fields
    )
    def delete(self, tenant_id):
        current_user = get_current_user()

        tenant = self.get_tenant(current_user, tenant_id)

        tenant.delete(current_user)
        return tenant
