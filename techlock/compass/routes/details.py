import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import DETAIL_CLAIM_SPEC as claim_spec
from ..models import (
    Detail,
    DetailListQueryParameters,
    DetailListQueryParametersSchema,
    DetailPageableSchema,
    DetailSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('details', __name__, url_prefix='/details')


@blp.route('')
class Details(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=DetailListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=DetailPageableSchema)
    def get(self, query_params: DetailListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET details')
        pageable_resp = Detail.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=DetailSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=DetailSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating detail', extra={'data': data})

        detail = Detail(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        detail.save(current_user, claims=claims, commit=not dry_run)

        return detail


@blp.route('/<detail_id>')
class DetailById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_detail(self, current_user: AuthInfo, claims: ClaimSet, detail_id: str):
        detail = Detail.get(
            current_user,
            detail_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return detail

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=DetailSchema)
    def get(self, detail_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting detail', extra={'id': detail_id})
        detail = self.get_detail(current_user, claims, detail_id)

        return detail

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=DetailSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=DetailSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, detail_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating detail', extra={'data': data})

        detail = self.get_detail(
            current_user,
            claims.filter_by_action('read'),
            detail_id,
        )

        for k, v in data.items():
            if hasattr(detail, k):
                setattr(detail, k, v)
            else:
                raise BadRequestException(f'Detail has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        detail.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return detail

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, detail_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting detail', extra={'id': detail_id})

        detail = self.get_detail(
            current_user,
            claims.filter_by_action('read'),
            detail_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        detail.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
