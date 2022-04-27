import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import UPLOAD_CLAIM_SPEC as claim_spec
from ..models import (
    Upload,
    UploadListQueryParameters,
    UploadListQueryParametersSchema,
    UploadPageableSchema,
    UploadSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('uploads', __name__, url_prefix='/uploads')


@blp.route('')
class Uploads(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=UploadListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=UploadPageableSchema)
    def get(self, query_params: UploadListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET uploads')
        pageable_resp = Upload.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=UploadSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=UploadSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating upload', extra={'data': data})

        upload = Upload(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        upload.save(current_user, claims=claims, commit=not dry_run)

        return upload


@blp.route('/<upload_id>')
class UploadById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_upload(self, current_user: AuthInfo, claims: ClaimSet, upload_id: str):
        upload = Upload.get(
            current_user,
            upload_id,
            claims=claims,
            raise_if_not_found=True,
        )

        return upload

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=UploadSchema)
    def get(self, upload_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting upload', extra={'id': upload_id})
        upload = self.get_upload(current_user, claims, upload_id)

        return upload

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=UploadSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=UploadSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, upload_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating upload', extra={'data': data})

        upload = self.get_upload(
            current_user,
            claims.filter_by_action('read'),
            upload_id,
        )

        for k, v in data.items():
            if hasattr(upload, k):
                setattr(upload, k, v)
            else:
                raise BadRequestException(f'Upload has no attribute: {k}')

        upload.save(
            current_user,
            claims=claims.filter_by_action('update'),
            commit=not dry_run,
        )

        return upload

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, upload_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting upload', extra={'id': upload_id})

        upload = self.get_upload(
            current_user,
            claims.filter_by_action('read'),
            upload_id,
        )

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        upload.delete(
            current_user,
            claims=claims.filter_by_action('delete'),
            commit=not dry_run,
        )

        return
