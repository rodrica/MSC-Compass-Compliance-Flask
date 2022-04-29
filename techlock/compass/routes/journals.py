import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

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


@blp.route('')
class Journals(MethodView):

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

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.save(current_user, claims=claims, commit=not dry_run)

        return journal


@blp.route('/<journal_id>')
class JournalById(MethodView):

    def get_journal(self, current_user: AuthInfo, claims: ClaimSet, journal_id: str):
        journal = Journal.get(
            current_user,
            journal_id,
            claims=claims,
            raise_if_not_found=True,
        )

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

        journal = self.get_journal(
            current_user,
            claims.filter_by_action('read'),
            journal_id,
        )

        for k, v in data.items():
            if hasattr(journal, k):
                setattr(journal, k, v)
            else:
                raise BadRequestException(f'Journal has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return journal

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, journal_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting journal', extra={'id': journal_id})

        journal = self.get_journal(
            current_user,
            claims.filter_by_action('read'),
            journal_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        journal.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
