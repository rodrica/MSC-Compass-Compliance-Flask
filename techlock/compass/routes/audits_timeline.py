import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import AUDIT_TIMELINE_CLAIM_SPEC as claim_spec
from ..models import (
    AuditTimeline,
    AuditTimelineListQueryParameters,
    AuditTimelineListQueryParametersSchema,
    AuditTimelinePageableSchema,
    AuditTimelineSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('audits_timeline', __name__, url_prefix='/audits_timeline')


@blp.route('')
class AuditTimelines(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=AuditTimelineListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=AuditTimelinePageableSchema)
    def get(self, query_params: AuditTimelineListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET audits_timeline')
        pageable_resp = AuditTimeline.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=AuditTimelineSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=AuditTimelineSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating audit', extra={'data': data})

        audit = AuditTimeline(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit.save(current_user, claims=claims, commit=not dry_run)

        return audit


@blp.route('/<audit_id>')
class AuditTimelineById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_audit(self, current_user: AuthInfo, claims: ClaimSet, audit_id: str):
        audit = AuditTimeline.get(
            current_user,
            audit_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return audit

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=AuditTimelineSchema)
    def get(self, audit_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting audit', extra={'id': audit_id})
        audit = self.get_audit(current_user, claims, audit_id)

        return audit

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=AuditTimelineSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=AuditTimelineSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, audit_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating audit', extra={'data': data})

        audit = self.get_audit(
            current_user,
            claims.filter_by_action('read'),
            audit_id,
        )

        for k, v in data.items():
            if hasattr(audit, k):
                setattr(audit, k, v)
            else:
                raise BadRequestException(f'AuditTimeline has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return audit

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, audit_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting audit', extra={'id': audit_id})

        audit = self.get_audit(
            current_user,
            claims.filter_by_action('read'),
            audit_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        audit.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
