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

from ..models import JOURNAL_CLAIM_SPEC as claim_spec
from ..models import (
    Journal,
    JournalListQueryParameters,
    JournalListQueryParametersSchema,
    JournalPageableSchema,
    JournalSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('journals', __name__, url_prefix='/journals')


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
class Journals(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=JournalListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=JournalPageableSchema)
    def get(self, query_params: JournalListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET journals')
        pageable_resp = Journal.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=JournalSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=JournalSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating journal', extra={'data': data})

        journal = Journal(**data)
        journal.claims_by_audience = set_claims_default_tenant(data,
                                                               current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.save(current_user, claims=claims, commit=not dry_run)

        return journal


@blp.route('/<journal_id>')
class JournalById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_journal(self, current_user: AuthInfo, claims: ClaimSet, journal_id: str):
        journal = Journal.get(current_user,
                              journal_id,
                              claims=claims,
                              raise_if_not_found=True)

        return journal

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=JournalSchema)
    def get(self, journal_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting journal', extra={'id': journal_id})
        journal = self.get_journal(current_user, claims, journal_id)

        return journal

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=JournalSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=JournalSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, journal_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating journal', extra={'data': data})

        journal = self.get_journal(current_user,
                                   claims.filter_by_action('read'),
                                   journal_id)

        for k, v in data.items():
            if hasattr(journal, k):
                setattr(journal, k, v)
            else:
                raise BadRequestException(f'Journal has no attribute: {k}')

        journal.claims_by_audience = set_claims_default_tenant(data,
                                                               current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.save(current_user,
                     claims=claims.filter_by_action('update'),
                     commit=not dry_run)

        return journal

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, journal_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting journal', extra={'id': journal_id})

        journal = self.get_journal(current_user,
                                   claims.filter_by_action('read'),
                                   journal_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.delete(current_user,
                       claims=claims.filter_by_action('delete'),
                       commit=not dry_run)

        return
