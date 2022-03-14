import logging
from dataclasses import asdict
from typing import Any, Dict
from uuid import UUID

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException, Claim
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import COMPLIANCE_CLAIM_SPEC as claim_spec
from ..models import (
    Compliance,
    ComplianceListQueryParameters,
    ComplianceListQueryParametersSchema,
    CompliancePageableSchema,
    ComplianceSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('compliances', __name__, url_prefix='/compliances')


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
class Compliances(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=CompliancePageableSchema)
    def get(self, query_params: ComplianceListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliances')
        pageable_resp = Compliance.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ComplianceSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating compliance', extra={'data': data})

        compliance = Compliance(**data)
        compliance.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.save(current_user, claims=claims, commit=not dry_run)

        return compliance


@blp.route('/<compliance_id>')
class ComplianceById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_compliance(self, current_user: AuthInfo, claims: ClaimSet, compliance_id: str):
        compliance = Compliance.get(current_user, compliance_id, claims=claims, raise_if_not_found=True)

        return compliance

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceSchema)
    def get(self, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting compliance', extra={'id': compliance_id})
        compliance = self.get_compliance(current_user, claims, compliance_id)

        return compliance

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ComplianceSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating compliance', extra={'data': data})

        compliance = self.get_compliance(current_user, claims.filter_by_action('read'), compliance_id)

        for k, v in data.items():
            if hasattr(compliance, k):
                setattr(compliance, k, v)
            else:
                raise BadRequestException(f'Compliance has no attribute: {k}')

        compliance.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)

        return compliance

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting compliance', extra={'id': compliance_id})

        compliance = self.get_compliance(current_user, claims.filter_by_action('read'), compliance_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)

        return
