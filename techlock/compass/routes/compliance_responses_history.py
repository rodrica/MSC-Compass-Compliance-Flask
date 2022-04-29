import logging

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.config import AuthInfo

from ..models import COMPLIANCE_RESPONSE_HISTORY_CLAIM_SPEC as claim_spec
from ..models import (
    ComplianceResponseHistory,
    ComplianceResponseHistoryListQueryParameters,
    ComplianceResponseHistoryListQueryParametersSchema,
    ComplianceResponseHistoryPageableSchema,
    ComplianceResponseHistorySchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint(
    'compliance_responses_history',
    __name__,
    url_prefix='/compliance_responses_history',
)


@blp.route('')
class ComplianceResponseHistorys(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=ComplianceResponseHistoryListQueryParametersSchema,
        location='query',
    )
    @blp.response(
        status_code=200,
        schema=ComplianceResponseHistoryPageableSchema,
    )
    def get(self, query_params: ComplianceResponseHistoryListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliance_responses_history')
        pageable_resp = ComplianceResponseHistory.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp


@blp.route('/<compliance_response_id>')
class ComplianceResponseHistoryById(MethodView):

    def get_compliance_response(self, current_user: AuthInfo, claims: ClaimSet, compliance_response_id: str):
        compliance_response = ComplianceResponseHistory.get(
            current_user,
            compliance_response_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return compliance_response

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceResponseHistorySchema)
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
