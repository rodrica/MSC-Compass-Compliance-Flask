import logging
from typing import Any, Dict

from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from flask.views import MethodView

from ..models import REPORT_VERSION_CLAIM_SPEC as claim_spec
from ..models import (
    ReportVersion,
    ReportVersionListQueryParameters,
    ReportVersionListQueryParametersSchema,
    ReportVersionPageableSchema,
    ReportVersionSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('report_versions', __name__, url_prefix='/report_versions')


@blp.route('')
class ReportVersions(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=ReportVersionListQueryParametersSchema,
                   location='query')
    @blp.response(status_code=200, schema=ReportVersionPageableSchema)
    def get(self, query_params: ReportVersionListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET report_versions')
        pageable_resp = ReportVersion.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=ReportVersionSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=ReportVersionSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating report_version', extra={'data': data})

        report_version = ReportVersion(**data)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_version.save(current_user, claims=claims, commit=not dry_run)

        return report_version


@blp.route('/<report_version_id>')
class ReportVersionById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)

    def get_report_version(self, current_user: AuthInfo, claims: ClaimSet, report_version_id: str):
        report_version = ReportVersion.get(current_user,
                                           report_version_id,
                                           claims=claims,
                                           raise_if_not_found=True)

        return report_version

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=ReportVersionSchema)
    def get(self, report_version_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting report_version', extra={'id': report_version_id})
        report_version = self.get_report_version(current_user,
                                                 claims,
                                                 report_version_id)

        return report_version

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=ReportVersionSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=ReportVersionSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, report_version_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating report_version', extra={'data': data})

        report_version = self.get_report_version(current_user,
                                                 claims.filter_by_action('read'),
                                                 report_version_id)

        for k, v in data.items():
            if hasattr(report_version, k):
                setattr(report_version, k, v)
            else:
                raise BadRequestException(f'ReportVersion has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_version.save(current_user,
                            claims=claims.filter_by_action('update'),
                            commit=not dry_run)

        return report_version

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, report_version_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting report_version', extra={'id': report_version_id})

        report_version = self.get_report_version(current_user,
                                                 claims.filter_by_action('read'),
                                                 report_version_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        report_version.delete(current_user,
                              claims=claims.filter_by_action('delete'),
                              commit=not dry_run)

        return
