import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.api import (
    BadRequestException, NotFoundException,
)
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)

from ..models import (
    Office, OfficeSchema, OfficePageableSchema,
    OfficeListQueryParameters, OfficeListQueryParametersSchema,
    OFFICE_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('offices', __name__, url_prefix='/offices')


@blp.route('')
class Offices(MethodView):

    @blp.arguments(OfficeListQueryParametersSchema, location='query')
    @blp.response(OfficePageableSchema)
    @access_required(
        'read', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: OfficeListQueryParameters):
        current_user = get_current_user()
        claims = get_request_claims()

        pageable_resp = Office.get_all(
            current_user,
            cursor=query_params.cursor,
            include_page_cursors=query_params.include_page_cursors,
            limit=query_params.limit,
            additional_conditions=query_params.get_filters(),
            claims=claims,
        )

        logger.info('GET offices', extra={
            'offices': pageable_resp.asdict()
        })

        return pageable_resp

    @blp.arguments(OfficeSchema)
    @blp.response(OfficeSchema, code=201)
    @access_required('create', 'offices')
    def post(self, data):
        current_user = get_current_user()
        logger.info('Creating Office', extra={'data': data})

        Office.validate(data)
        office = Office(**data)
        office.save(current_user)

        return office


@blp.route('/<office_id>')
class OfficeById(MethodView):

    @blp.response(OfficeSchema)
    @access_required(
        'read', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def get(self, office_id):
        current_user = get_current_user()
        claims = get_request_claims()

        office = Office.get(current_user, office_id)
        # If no access, return 404
        if office is None or not can_access(office, claims):
            raise NotFoundException('No office found for id = {}'.format(office_id))

        return office

    @blp.arguments(OfficeSchema)
    @blp.response(OfficeSchema)
    @access_required(
        'update', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, office_id):
        current_user = get_current_user()
        claims = get_request_claims()
        logger.debug('Updating Office', extra={'data': data})

        Office.validate(data, validate_required_fields=False)
        office = Office.get(current_user, office_id)
        if office is None or not can_access(office, claims):
            raise NotFoundException('No office found for id = {}'.format(office_id))

        for k, v in data.items():
            if hasattr(office, k):
                setattr(office, k, v)
            else:
                raise BadRequestException('Office has no attribute: %s' % k)
        office.save(current_user)
        return office

    @blp.response(OfficeSchema, code=204)
    @access_required(
        'delete', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def delete(self, office_id):
        current_user = get_current_user()
        claims = get_request_claims()

        office = Office.get(current_user, office_id)
        if office is None or not can_access(office, claims):
            raise NotFoundException('No office found for id = {}'.format(office_id))

        office.delete(current_user)
        return office
