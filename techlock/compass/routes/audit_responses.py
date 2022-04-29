import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import AUDIT_RESPONSE_CLAIM_SPEC as claim_spec
from ..models import (
    AuditResponse,
    AuditResponseListQueryParameters,
    AuditResponseListQueryParametersSchema,
    AuditResponsePageableSchema,
    AuditResponseSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('audit_responses', __name__, url_prefix='/audit_responses')


@blp.route('')
class AuditResponses(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=AuditResponseListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=AuditResponsePageableSchema)
    def get(self, query_params: AuditResponseListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET audit_responses')
        pageable_resp = AuditResponse.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=AuditResponseSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=AuditResponseSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating audit_history', extra={'data': data})

        audit_history = AuditResponse(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit_history.save(current_user, claims=claims, commit=not dry_run)

        return audit_history


@blp.route('/<audit_history_id>')
class AuditResponseById(MethodView):

    def get_audit_history(self, current_user: AuthInfo, claims: ClaimSet, audit_history_id: str):
        audit_history = AuditResponse.get(
            current_user,
            audit_history_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return audit_history

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=AuditResponseSchema)
    def get(self, audit_history_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting audit_history', extra={'id': audit_history_id})
        audit_history = self.get_audit_history(
            current_user,
            claims,
            audit_history_id,
        )

        return audit_history

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=AuditResponseSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=AuditResponseSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, audit_history_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating audit_history', extra={'data': data})

        audit_history = self.get_audit_history(
            current_user,
            claims.filter_by_action('read'),
            audit_history_id,
        )

        for k, v in data.items():
            if hasattr(audit_history, k):
                setattr(audit_history, k, v)
            else:
                raise BadRequestException(f'AuditResponse has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit_history.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return audit_history

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, audit_history_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting audit_history', extra={'id': audit_history_id})

        audit_history = self.get_audit_history(
            current_user,
            claims.filter_by_action('read'),
            audit_history_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit_history.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
