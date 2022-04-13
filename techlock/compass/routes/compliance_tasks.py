import logging
from dataclasses import asdict
from typing import Any, Dict

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException, Claim
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import COMPLIANCE_TASK_CLAIM_SPEC as claim_spec
from ..models import (
    ComplianceTask,
    ComplianceTaskListQueryParameters,
    ComplianceTaskListQueryParametersSchema,
    ComplianceTaskPageableSchema,
    ComplianceTaskSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('compliance_tasks', __name__, url_prefix='/compliance_tasks')


def set_claims_default_tenant(data: dict, default_tenant_id: str):
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
class ComplianceTasks(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceTaskListQueryParametersSchema,
                   location='query')
    @blp.response(status_code=200, schema=ComplianceTaskPageableSchema)
    def get(self, query_params: ComplianceTaskListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliance_tasks')
        pageable_resp = ComplianceTask.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceTaskSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ComplianceTaskSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating compliance_task', extra={'data': data})

        compliance_task = ComplianceTask(**data)
        compliance_task.claims_by_audience = set_claims_default_tenant(data,
                                                                       current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_task.save(current_user, claims=claims, commit=not dry_run)

        return compliance_task


@blp.route('/<compliance_task_id>')
class ComplianceTaskById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_compliance_task(self, current_user: AuthInfo, claims: ClaimSet, compliance_task_id: str):
        compliance_task = ComplianceTask.get(current_user,
                                             compliance_task_id,
                                             claims=claims,
                                             raise_if_not_found=True)

        return compliance_task

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceTaskSchema)
    def get(self, compliance_task_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting compliance_task',
                    extra={'id': compliance_task_id})
        compliance_task = self.get_compliance_task(current_user,
                                                   claims,
                                                   compliance_task_id)

        return compliance_task

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ComplianceTaskSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ComplianceTaskSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, compliance_task_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating compliance_task', extra={'data': data})

        compliance_task = self.get_compliance_task(current_user,
                                                   claims.filter_by_action('read'),
                                                   compliance_task_id)

        for k, v in data.items():
            if hasattr(compliance_task, k):
                setattr(compliance_task, k, v)
            else:
                raise BadRequestException(f'ComplianceTask has no attribute: {k}')

        compliance_task.claims_by_audience = set_claims_default_tenant(data,
                                                                       current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_task.save(current_user,
                             claims=claims.filter_by_action('update'),
                             commit=not dry_run)

        return compliance_task

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, compliance_task_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting compliance_task',
                    extra={'id': compliance_task_id})

        compliance_task = self.get_compliance_task(current_user,
                                                   claims.filter_by_action('read'),
                                                   compliance_task_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        compliance_task.delete(current_user,
                               claims=claims.filter_by_action('delete'),
                               commit=not dry_run)

        return
