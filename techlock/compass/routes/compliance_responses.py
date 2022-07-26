import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import COMPLIANCE_RESPONSE_CLAIM_SPEC as claim_spec
from ..models import (
    ComplianceResponse,
    ComplianceResponseListQueryParameters,
    ComplianceResponseListQueryParametersSchema,
    ComplianceResponsePageableSchema,
    ComplianceResponseSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint(
    'compliance_responses',
    __name__,
    url_prefix='/compliance_responses',
)


@blp.route('')
class ComplianceResponses(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=ComplianceResponseListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=ComplianceResponsePageableSchema)
    def get(self, query_params: ComplianceResponseListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliance_responses')
        pageable_resp = ComplianceResponse.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceResponseSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ComplianceResponseSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating compliance_response', extra={'data': data})

        compliance_response = ComplianceResponse(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_response.save(
            current_user,
            claims=claims,
            commit=not dry_run,
        )

        return compliance_response


@blp.route('/<compliance_response_id>')
class ComplianceResponseById(MethodView):

    def get_compliance_response(self, current_user: AuthInfo, claims: ClaimSet, compliance_response_id: str):
        compliance_response = ComplianceResponse.get(
            current_user,
            compliance_response_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return compliance_response

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceResponseSchema)
    def get(self, compliance_response_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info(
            'Getting compliance_response',
            extra={'id': compliance_response_id},
        )
        compliance_response = self.get_compliance_response(
            current_user,
            claims,
            compliance_response_id,
        )

        return compliance_response

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceResponseSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ComplianceResponseSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, compliance_response_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating compliance_response', extra={'data': data})

        compliance_response = self.get_compliance_response(
            current_user,
            claims.filter_by_action('read'),
            compliance_response_id,
        )

        for k, v in data.items():
            if hasattr(compliance_response, k):
                setattr(compliance_response, k, v)
            else:
                raise BadRequestException(f'ComplianceResponse has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_response.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return compliance_response

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, compliance_response_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info(
            'Deleting compliance_response',
            extra={'id': compliance_response_id},
        )

        compliance_response = self.get_compliance_response(
            current_user,
            claims.filter_by_action('read'),
            compliance_response_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_response.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
