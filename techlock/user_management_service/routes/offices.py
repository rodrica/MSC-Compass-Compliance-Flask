import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint
from typing import List, Union
from uuid import UUID

from techlock.common.api import (
    BadRequestException, NotFoundException,
)
from techlock.common.config import AuthInfo
from techlock.common.api.jwt_authorization import (
    access_required,
    get_request_claims,
    can_access,
)
from techlock.common.orm.sqlalchemy import BaseModel

from ..models import (
    Department,
    Office, OfficeSchema, OfficePageableSchema,
    OfficeListQueryParameters, OfficeListQueryParametersSchema,
    OFFICE_CLAIM_SPEC,
)

logger = logging.getLogger(__name__)

blp = Blueprint('offices', __name__, url_prefix='/offices')


def _get_items_from_id_list(current_user: AuthInfo, id_list: List[Union[str, UUID]], ormClass: BaseModel):
    items = list()
    if not id_list:
        return items

    for entity_id in id_list:
        items.append(ormClass.get(current_user, entity_id=entity_id, raise_if_not_found=True))

    return items


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
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(current_user),
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

        data['departments'] = _get_items_from_id_list(current_user, data.pop('department_ids', None), Department)

        office = Office(**data)
        office.save(current_user)

        return office


@blp.route('/<office_id>')
class OfficeById(MethodView):

    def get_office(self, current_user: AuthInfo, office_id: str):
        claims = get_request_claims()

        office = Office.get(current_user, office_id)
        # If no access, return 404
        if office is None or not can_access(office, claims):
            raise NotFoundException('No office found for id = {}'.format(office_id))

        return office

    @blp.response(OfficeSchema)
    @access_required(
        'read', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def get(self, office_id):
        current_user = get_current_user()

        office = self.get_office(current_user, office_id)

        return office

    @blp.arguments(OfficeSchema)
    @blp.response(OfficeSchema)
    @access_required(
        'update', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, office_id):
        current_user = get_current_user()
        logger.debug('Updating Office', extra={'data': data})

        office = self.get_office(current_user, office_id)

        # Validate that items exist and get actual items
        data['departments'] = _get_items_from_id_list(current_user, data.pop('department_ids', None), Department)

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

        office = self.get_office(current_user, office_id)

        office.delete(current_user)
        return office
