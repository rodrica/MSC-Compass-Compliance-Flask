import logging
from typing import Any, Dict

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import COMMENT_CLAIM_SPEC as claim_spec
from ..models import (
    Comment,
    CommentListQueryParameters,
    CommentListQueryParametersSchema,
    CommentPageableSchema,
    CommentSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('comments', __name__, url_prefix='/comments')


@blp.route('')
class Comments(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=CommentListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=CommentPageableSchema)
    def get(self, query_params: CommentListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET comments')
        pageable_resp = Comment.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=CommentSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=CommentSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating comment', extra={'data': data})

        comment = Comment(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        comment.save(current_user, claims=claims, commit=not dry_run)

        return comment


@blp.route('/<comment_id>')
class CommentById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_comment(self, current_user: AuthInfo, claims: ClaimSet, comment_id: str):
        comment = Comment.get(current_user,
                              comment_id,
                              claims=claims,
                              raise_if_not_found=True)

        return comment

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=CommentSchema)
    def get(self, comment_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting comment', extra={'id': comment_id})
        comment = self.get_comment(current_user, claims, comment_id)

        return comment

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=CommentSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=CommentSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, comment_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating comment', extra={'data': data})

        comment = self.get_comment(current_user,
                                   claims.filter_by_action('read'),
                                   comment_id)

        for k, v in data.items():
            if hasattr(comment, k):
                setattr(comment, k, v)
            else:
                raise BadRequestException(f'Comment has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        comment.save(current_user,
                     claims=claims.filter_by_action('update'),
                     commit=not dry_run)

        return comment

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, comment_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting comment', extra={'id': comment_id})

        comment = self.get_comment(current_user,
                                   claims.filter_by_action('read'),
                                   comment_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        comment.delete(current_user,
                       claims=claims.filter_by_action('delete'),
                       commit=not dry_run)

        return
