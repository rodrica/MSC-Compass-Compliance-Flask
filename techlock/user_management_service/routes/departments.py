import logging
from typing import List

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import (
    access_required,
    get_current_user_with_claims,
)
from techlock.common.api.auth.claim import Claim
from techlock.common.config import AuthInfo

from ..models import (
    DEPARTMENT_CLAIM_SPEC,
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

    @blp.arguments(schema=DepartmentListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=DepartmentPageableSchema)
    @access_required(
        'read', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: DepartmentListQueryParameters):
        current_user, claims = get_current_user_with_claims()

        pageable_resp = Department.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(),
            claims=claims,
        )

        logger.info('GET departments', extra={
            'departments': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(schema=DepartmentSchema)
    @blp.response(status_code=201, schema=DepartmentSchema)
    @access_required('create', 'departments')
    def post(self, data):
        current_user, claims = get_current_user_with_claims()

        logger.info('Creating Department', extra={'data': data})

        department = Department(**data)
        department.save(current_user, claims=claims)

        return department


@blp.route('/<department_id>')
class DepartmentById(MethodView):

    def get_department(self, current_user: AuthInfo, claims: List[Claim], department_id: str):
        department = Department.get(current_user, department_id, claims=claims, raise_if_not_found=True)

        return department

    @blp.response(status_code=200, schema=DepartmentSchema)
    @access_required(
        'read', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def get(self, department_id):
        current_user, claims = get_current_user_with_claims()

        department = self.get_department(current_user, claims, department_id)

        return department

    @blp.arguments(schema=DepartmentSchema)
    @blp.response(status_code=200, schema=DepartmentSchema)
    @access_required(
        'update', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def put(self, data, department_id):
        current_user, claims = get_current_user_with_claims()

        logger.debug('Updating Department', extra={'data': data})

        department = self.get_department(current_user, claims, department_id)

        for k, v in data.items():
            if hasattr(department, k):
                setattr(department, k, v)
            else:
                raise BadRequestException('Department has no attribute: %s' % k)
        department.save(current_user, claims=claims)
        return department

    @blp.response(status_code=204, schema=DepartmentSchema)
    @access_required(
        'delete', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def delete(self, department_id):
        current_user, claims = get_current_user_with_claims()

        department = self.get_department(current_user, claims, department_id)

        department.delete(current_user)
        return department
