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

from ..models import REPORT_NODE_CLAIM_SPEC as claim_spec
from ..models import (
    ReportNode,
    ReportNodeListQueryParameters,
    ReportNodeListQueryParametersSchema,
    ReportNodePageableSchema,
    ReportNodeSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('report_nodes', __name__, url_prefix='/report_nodes')


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
class ReportNodes(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ReportNodeListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=ReportNodePageableSchema)
    def get(self, query_params: ReportNodeListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET report_nodes')
        pageable_resp = ReportNode.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ReportNodeSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ReportNodeSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating report_node', extra={'data': data})

        report_node = ReportNode(**data)
        report_node.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_node.save(current_user, claims=claims, commit=not dry_run)

        return report_node


@blp.route('/<report_node_id>')
class ReportNodeById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_report_node(self, current_user: AuthInfo, claims: ClaimSet, report_node_id: str):
        report_node = ReportNode.get(current_user, report_node_id, claims=claims, raise_if_not_found=True)

        return report_node

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ReportNodeSchema)
    def get(self, report_node_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting report_node', extra={'id': report_node_id})
        report_node = self.get_report_node(current_user, claims, report_node_id)

        return report_node

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ReportNodeSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ReportNodeSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, report_node_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating report_node', extra={'data': data})

        report_node = self.get_report_node(current_user, claims.filter_by_action('read'), report_node_id)

        for k, v in data.items():
            if hasattr(report_node, k):
                setattr(report_node, k, v)
            else:
                raise BadRequestException(f'ReportNode has no attribute: {k}')

        report_node.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_node.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)

        return report_node

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, report_node_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting report_node', extra={'id': report_node_id})

        report_node = self.get_report_node(current_user, claims.filter_by_action('read'), report_node_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_node.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)

        return
