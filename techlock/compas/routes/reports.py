import logging
from dataclasses import asdict
from typing import Any, Dict
from uuid import UUID

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException, Claim, NotFoundException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import REPORT_CLAIM_SPEC as claim_spec
from ..models import (
    Report,
    ReportListQueryParameters,
    ReportListQueryParametersSchema,
    ReportPageableSchema,
    ReportSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('reports', __name__, url_prefix='/reports')


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
class Reports(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ReportListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=ReportPageableSchema)
    def get(self, query_params: ReportListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET reports')
        pageable_resp = Report.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ReportSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ReportSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating report', extra={'data': data})

        report = Report(**data)
        report.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report.save(current_user, claims=claims, commit=not dry_run)

        return report


@blp.route('/<report_id>')
class ReportById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_report(self, current_user: AuthInfo, claims: ClaimSet, report_id: str):
        report = Report.get(current_user, report_id, claims=claims, raise_if_not_found=True)

        return report

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ReportSchema)
    def get(self, report_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting report', extra={'id': report_id})
        report = self.get_report(current_user, claims, report_id)

        return report

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ReportSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ReportSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, report_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating report', extra={'data': data})

        report = self.get_report(current_user, claims.filter_by_action('read'), report_id)

        for k, v in data.items():
            if hasattr(report, k):
                setattr(report, k, v)
            else:
                raise BadRequestException(f'Report has no attribute: {k}')

        report.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)

        return report

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, report_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting report', extra={'id': report_id})

        report = self.get_report(current_user, claims.filter_by_action('read'), report_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)

        return
