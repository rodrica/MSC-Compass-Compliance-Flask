import logging
from typing import Any, Dict

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import EVENT_CLAIM_SPEC as claim_spec
from ..models import (
    Event,
    EventListQueryParameters,
    EventListQueryParametersSchema,
    EventPageableSchema,
    EventSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('events', __name__, url_prefix='/events')


@blp.route('')
class Events(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=EventListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=EventPageableSchema)
    def get(self, query_params: EventListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET events')
        pageable_resp = Event.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=EventSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=EventSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating event', extra={'data': data})

        event = Event(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        event.save(current_user, claims=claims, commit=not dry_run)

        return event


@blp.route('/<event_id>')
class EventById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_event(self, current_user: AuthInfo, claims: ClaimSet, event_id: str):
        event = Event.get(current_user,
                          event_id,
                          claims=claims,
                          raise_if_not_found=True)

        return event

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=EventSchema)
    def get(self, event_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting event', extra={'id': event_id})
        event = self.get_event(current_user, claims, event_id)

        return event

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=EventSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=EventSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, event_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating event', extra={'data': data})

        event = self.get_event(current_user,
                               claims.filter_by_action('read'),
                               event_id)

        for k, v in data.items():
            if hasattr(event, k):
                setattr(event, k, v)
            else:
                raise BadRequestException(f'Event has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        event.save(current_user,
                   claims=claims.filter_by_action('update'),
                   commit=not dry_run)

        return event

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, event_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting event', extra={'id': event_id})

        event = self.get_event(current_user,
                               claims.filter_by_action('read'),
                               event_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        event.delete(current_user,
                     claims=claims.filter_by_action('delete'),
                     commit=not dry_run)

        return
