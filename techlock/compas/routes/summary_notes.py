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

from ..models import SUMMARY_NOTE_CLAIM_SPEC as claim_spec
from ..models import (
    SummaryNote,
    SummaryNoteListQueryParameters,
    SummaryNoteListQueryParametersSchema,
    SummaryNotePageableSchema,
    SummaryNoteSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('summary_notes', __name__, url_prefix='/summary_notes')


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
class SummaryNotes(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=SummaryNoteListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=SummaryNotePageableSchema)
    def get(self, query_params: SummaryNoteListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET summary_notes')
        pageable_resp = SummaryNote.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=SummaryNoteSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=SummaryNoteSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating summary_note', extra={'data': data})

        summary_note = SummaryNote(**data)
        summary_note.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        summary_note.save(current_user, claims=claims, commit=not dry_run)

        return summary_note


@blp.route('/<summary_note_id>')
class SummaryNoteById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_summary_note(self, current_user: AuthInfo, claims: ClaimSet, summary_note_id: str):
        summary_note = SummaryNote.get(current_user, summary_note_id, claims=claims, raise_if_not_found=True)

        return summary_note

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=SummaryNoteSchema)
    def get(self, summary_note_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting summary_note', extra={'id': summary_note_id})
        summary_note = self.get_summary_note(current_user, claims, summary_note_id)

        return summary_note

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=SummaryNoteSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=SummaryNoteSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, summary_note_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating summary_note', extra={'data': data})

        summary_note = self.get_summary_note(current_user, claims.filter_by_action('read'), summary_note_id)

        for k, v in data.items():
            if hasattr(summary_note, k):
                setattr(summary_note, k, v)
            else:
                raise BadRequestException(f'SummaryNote has no attribute: {k}')

        summary_note.claims_by_audience = set_claims_default_tenant(data, current_user.tenant_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        summary_note.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)

        return summary_note

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, summary_note_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting summary_note', extra={'id': summary_note_id})

        summary_note = self.get_summary_note(current_user, claims.filter_by_action('read'), summary_note_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        summary_note.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)

        return
