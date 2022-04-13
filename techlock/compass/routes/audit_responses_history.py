import logging
from dataclasses import asdict
from uuid import UUID

from flask_smorest import Blueprint
from techlock.common.api import Claim
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import AUDIT_RESPONSE_CLAIM_SPEC as claim_spec
from ..models import (
    AuditResponseHistory,
    AuditResponseHistoryListQueryParameters,
    AuditResponseHistoryListQueryParametersSchema,
    AuditResponseHistoryPageableSchema,
    AuditResponseHistorySchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('audit_responses_history',
                __name__,
                url_prefix='/audit_responses_history')


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
class AuditResponseHistorys(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=AuditResponseHistoryListQueryParametersSchema,
                   location='query')
    @blp.response(status_code=200, schema=AuditResponseHistoryPageableSchema)
    def get(self, query_params: AuditResponseHistoryListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET audit_responses_history')
        pageable_resp = AuditResponseHistory.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp


@blp.route('/<audit_history_id>')
class AuditResponseHistoryById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_audit_history(self, current_user: AuthInfo, claims: ClaimSet, audit_history_id: str):
        audit_history = AuditResponseHistory.get(current_user,
                                                 audit_history_id,
                                                 claims=claims,
                                                 raise_if_not_found=True)

        return audit_history

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=AuditResponseHistorySchema)
    def get(self, audit_history_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting audit_history', extra={'id': audit_history_id})
        audit_history = self.get_audit_history(current_user,
                                               claims,
                                               audit_history_id)

        return audit_history
