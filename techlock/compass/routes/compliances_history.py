import logging

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.config import AuthInfo

from ..models import COMPLIANCE_HISTORY_CLAIM_SPEC as claim_spec
from ..models import (
    ComplianceHistory,
    ComplianceHistoryListQueryParameters,
    ComplianceHistoryListQueryParametersSchema,
    ComplianceHistoryPageableSchema,
    ComplianceHistorySchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint(
    'compliances_history',
    __name__,
    url_prefix='/compliances_history',
)


@blp.route('')
class ComplianceHistorys(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(
        schema=ComplianceHistoryListQueryParametersSchema,
        location='query',
    )
    @blp.response(status_code=200, schema=ComplianceHistoryPageableSchema)
    def get(self, query_params: ComplianceHistoryListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET compliances_history')
        pageable_resp = ComplianceHistory.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp


@blp.route('/<compliance_id>')
class ComplianceHistoryById(MethodView):

    def get_compliance(self, current_user: AuthInfo, claims: ClaimSet, compliance_id: str):
        compliance = ComplianceHistory.get(
            current_user,
            compliance_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return compliance

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ComplianceHistorySchema)
    def get(self, compliance_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting compliance', extra={'id': compliance_id})
        compliance = self.get_compliance(current_user, claims, compliance_id)

        return compliance
