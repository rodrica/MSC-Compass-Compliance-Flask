import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import (
    BadRequestException, NotFoundException,
    PageableQueryParametersSchema,
)
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)

from ..models import (
    Department, DepartmentSchema, DepartmentPageableSchema,
    DEPARTMENT_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('departments', __name__, url_prefix='/departments')


@blp.route('')
class Departments(MethodView):

    @blp.arguments(PageableQueryParametersSchema, location='query')
    @blp.response(DepartmentPageableSchema)
    @access_required(
        'read', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def get(self, args):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = Department.get_all(
            current_user,
            limit=args.get('limit', 50),
            start_key=args.get('start_key'),
            claims=claims,
        )

        logger.info('GET departments', extra={
            'departments': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(DepartmentSchema)
    @blp.response(DepartmentSchema, code=201)
    @access_required('create', 'departments')
    def post(self, data):
        current_user = get_current_user()
        logger.info('Creating Department', extra={'data': data})

        Department.validate(data)
        department = Department(**data)
        department.save(current_user)

        return department


@blp.route('/<department_id>')
class DepartmentById(MethodView):

    @blp.response(DepartmentSchema)
    @access_required(
        'read', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def get(self, department_id):
        current_user = get_current_user()
        claims = get_request_claims()

        department = Department.get(current_user, department_id)
        # If no access, return 404
        if department is None or not can_access(department, claims):
            raise NotFoundException('No department found for id = {}'.format(department_id))

        return department

    @blp.arguments(DepartmentSchema)
    @blp.response(DepartmentSchema)
    @access_required(
        'update', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def put(self, data, department_id):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.debug('Updating Department', extra={'data': data})

        Department.validate(data, validate_required_fields=False)
        department = Department.get(current_user, department_id)
        if department is None or not can_access(department, claims):
            raise NotFoundException('No department found for id = {}'.format(department_id))

        for k, v in data.items():
            if hasattr(department, k):
                setattr(department, k, v)
            else:
                raise BadRequestException('Department has no attribute: %s' % k)
        department.save(current_user)
        return department

    @blp.response(DepartmentSchema, code=204)
    @access_required(
        'delete', 'departments',
        allowed_filter_fields=DEPARTMENT_CLAIM_SPEC.filter_fields
    )
    def delete(self, department_id):
        current_user = get_current_user()
        claims = get_request_claims()

        department = Department.get(current_user, department_id)
        if department is None or not can_access(department, claims):
            raise NotFoundException('No department found for id = {}'.format(department_id))

        department.delete(current_user)
        return department
