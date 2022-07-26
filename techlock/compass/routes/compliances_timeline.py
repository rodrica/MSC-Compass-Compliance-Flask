import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import COMPLIANCE_TIMELINE_CLAIM_SPEC as claim_spec
from ..models import (
    ComplianceTimeline,
    ComplianceTimelineListQueryParameters,
    ComplianceTimelineListQueryParametersSchema,
    ComplianceTimelinePageableSchema,
    ComplianceTimelineSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint(
    'compliances_timeline',
    __name__,
    url_prefix='/compliances_timeline',
)


@blp.route('')
class ComplianceTimelines(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=ComplianceTimelineListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=ComplianceTimelinePageableSchema)
    def get(self, query_params: ComplianceTimelineListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliances_timeline')
        pageable_resp = ComplianceTimeline.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceTimelineSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ComplianceTimelineSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating compliance', extra={'data': data})

        compliance = ComplianceTimeline(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.save(current_user, claims=claims, commit=not dry_run)

        return compliance


@blp.route('/<compliance_id>')
class ComplianceTimelineById(MethodView):

    def get_compliance(self, current_user: AuthInfo, claims: ClaimSet, compliance_id: str):
        compliance = ComplianceTimeline.get(
            current_user,
            compliance_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return compliance

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceTimelineSchema)
    def get(self, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting compliance', extra={'id': compliance_id})
        compliance = self.get_compliance(current_user, claims, compliance_id)

        return compliance

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceTimelineSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ComplianceTimelineSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating compliance', extra={'data': data})

        compliance = self.get_compliance(
            current_user,
            claims.filter_by_action('read'),
            compliance_id,
        )

        for k, v in data.items():
            if hasattr(compliance, k):
                setattr(compliance, k, v)
            else:
                raise BadRequestException(f'ComplianceTimeline has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return compliance

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting compliance', extra={'id': compliance_id})

        compliance = self.get_compliance(
            current_user,
            claims.filter_by_action('read'),
            compliance_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
