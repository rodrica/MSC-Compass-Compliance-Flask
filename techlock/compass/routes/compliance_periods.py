import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import COMPLIANCE_PERIOD_CLAIM_SPEC as claim_spec
from ..models import (
    CompliancePeriod,
    CompliancePeriodListQueryParameters,
    CompliancePeriodListQueryParametersSchema,
    CompliancePeriodPageableSchema,
    CompliancePeriodSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint(
    'compliance_periods',
    __name__,
    url_prefix='/compliance_periods',
)


@blp.route('')
class CompliancePeriods(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=CompliancePeriodListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=CompliancePeriodPageableSchema)
    def get(self, query_params: CompliancePeriodListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliance_periods')
        pageable_resp = CompliancePeriod.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=CompliancePeriodSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=CompliancePeriodSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating compliance_period', extra={'data': data})

        compliance_period = CompliancePeriod(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_period.save(current_user, claims=claims, commit=not dry_run)

        return compliance_period


@blp.route('/<compliance_period_id>')
class CompliancePeriodById(MethodView):

    def get_compliance_period(self, current_user: AuthInfo, claims: ClaimSet, compliance_period_id: str):
        compliance_period = CompliancePeriod.get(
            current_user,
            compliance_period_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return compliance_period

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=CompliancePeriodSchema)
    def get(self, compliance_period_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info(
            'Getting compliance_period',
            extra={'id': compliance_period_id},
        )
        compliance_period = self.get_compliance_period(
            current_user,
            claims,
            compliance_period_id,
        )

        return compliance_period

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=CompliancePeriodSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=CompliancePeriodSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, compliance_period_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating compliance_period', extra={'data': data})

        compliance_period = self.get_compliance_period(
            current_user,
            claims.filter_by_action('read'),
            compliance_period_id,
        )

        for k, v in data.items():
            if hasattr(compliance_period, k):
                setattr(compliance_period, k, v)
            else:
                raise BadRequestException(f'CompliancePeriod has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_period.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return compliance_period

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, compliance_period_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info(
            'Deleting compliance_period',
            extra={'id': compliance_period_id},
        )

        compliance_period = self.get_compliance_period(
            current_user,
            claims.filter_by_action('read'),
            compliance_period_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_period.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
