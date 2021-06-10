import logging
from typing import Any, Dict

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo

from ..models import DEPARTMENT_CLAIM_SPEC as claim_spec
from ..models import (
    Department,
    DepartmentListQueryParameters,
    DepartmentListQueryParametersSchema,
    DepartmentPageableSchema,
    DepartmentSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('departments', __name__, url_prefix='/departments')


@blp.route('')
class Departments(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=DepartmentListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=DepartmentPageableSchema)
    def get(self, query_params: DepartmentListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET departments')
        pageable_resp = Department.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        return pageable_resp

    @access_required('create', claim_spec=claim_spec)
    @blp.arguments(schema=DepartmentSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=DepartmentSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating department', extra={'data': data})

        department = Department(**data)
        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        department.save(current_user, claims=claims, commit=not dry_run)

        return department


@blp.route('/<department_id>')
class DepartmentById(MethodView):

    def get_department(self, current_user: AuthInfo, claims: ClaimSet, department_id: str):
        department = Department.get(current_user, department_id, claims=claims, raise_if_not_found=True)

        return department

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=DepartmentSchema)
    def get(self, department_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting department', extra={'id': department_id})
        department = self.get_department(current_user, claims, department_id)

        return department

    @access_required(['read', 'update'], claim_spec=claim_spec)
    @blp.arguments(schema=DepartmentSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=DepartmentSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, department_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating department', extra={'data': data})

        department = self.get_department(current_user, claims.filter_by_action('read'), department_id)

        for k, v in data.items():
            if hasattr(department, k):
                setattr(department, k, v)
            else:
                raise BadRequestException(f'Department has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        department.save(current_user, claims=claims.filter_by_action('update'), commit=not dry_run)
        return department

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, department_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting department', extra={'id': department_id})
        department = self.get_department(current_user, claims.filter_by_action('read'), department_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        department.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)
        return
