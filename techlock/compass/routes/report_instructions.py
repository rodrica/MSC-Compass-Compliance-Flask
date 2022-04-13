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

from ..models import REPORT_INSTRUCTION_CLAIM_SPEC as claim_spec
from ..models import (
    ReportInstruction,
    ReportInstructionListQueryParameters,
    ReportInstructionListQueryParametersSchema,
    ReportInstructionPageableSchema,
    ReportInstructionSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('report_instructions',
                __name__,
                url_prefix='/report_instructions')


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
class ReportInstructions(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ReportInstructionListQueryParametersSchema,
                   location='query')
    @blp.response(status_code=200, schema=ReportInstructionPageableSchema)
    def get(self, query_params: ReportInstructionListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET report_instructions')
        pageable_resp = ReportInstruction.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ReportInstructionSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ReportInstructionSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating report_instruction', extra={'data': data})

        report_instruction = ReportInstruction(**data)
        report_instruction.claims_by_audience = set_claims_default_tenant(data,
                                                                          current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_instruction.save(current_user,
                                claims=claims,
                                commit=not dry_run)

        return report_instruction


@blp.route('/<report_instruction_id>')
class ReportInstructionById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_report_instruction(self, current_user: AuthInfo, claims: ClaimSet, report_instruction_id: str):
        report_instruction = ReportInstruction.get(current_user,
                                                   report_instruction_id,
                                                   claims=claims,
                                                   raise_if_not_found=True)

        return report_instruction

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ReportInstructionSchema)
    def get(self, report_instruction_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting report_instruction',
                    extra={'id': report_instruction_id})
        report_instruction = self.get_report_instruction(current_user,
                                                         claims,
                                                         report_instruction_id)

        return report_instruction

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ReportInstructionSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ReportInstructionSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, report_instruction_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating report_instruction', extra={'data': data})

        report_instruction = self.get_report_instruction(current_user,
                                                         claims.filter_by_action('read'),
                                                         report_instruction_id)

        for k, v in data.items():
            if hasattr(report_instruction, k):
                setattr(report_instruction, k, v)
            else:
                raise BadRequestException(f'ReportInstruction has no attribute: {k}')

        report_instruction.claims_by_audience = set_claims_default_tenant(data,
                                                                          current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_instruction.save(current_user,
                                claims=claims.filter_by_action('update'),
                                commit=not dry_run)

        return report_instruction

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, report_instruction_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting report_instruction',
                    extra={'id': report_instruction_id})

        report_instruction = self.get_report_instruction(current_user,
                                                         claims.filter_by_action('read'),
                                                         report_instruction_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_instruction.delete(current_user,
                                  claims=claims.filter_by_action('delete'),
                                  commit=not dry_run)

        return
