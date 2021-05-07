import logging
from typing import List, Union
from uuid import UUID

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import (
    access_required,
    get_current_user_with_claims,
)
from techlock.common.api.auth.claim import Claim
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import BaseModel

from ..models import (
    OFFICE_CLAIM_SPEC,
    Department,
    Office,
    OfficeListQueryParameters,
    OfficeListQueryParametersSchema,
    OfficePageableSchema,
    OfficeSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('offices', __name__, url_prefix='/offices')


def _get_items_from_id_list(
    current_user: AuthInfo,
    claims: List[Claim],
    id_list: List[Union[str, UUID]],
    orm_class: BaseModel
):
    items = list()
    if not id_list:
        return items

    for entity_id in id_list:
        items.append(orm_class.get(current_user, entity_id=entity_id, claims=claims, raise_if_not_found=True))

    return items


@blp.route('')
class Offices(MethodView):

    @blp.arguments(schema=OfficeListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=OfficePageableSchema)
    @access_required(
        'read', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def get(self, query_params: OfficeListQueryParameters):
        current_user, claims = get_current_user_with_claims()

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

    @blp.arguments(schema=OfficeSchema)
    @blp.response(status_code=201, schema=OfficeSchema)
    @access_required('create', 'offices')
    def post(self, data):
        current_user, claims = get_current_user_with_claims()
        logger.info('Creating Office', extra={'data': data})

        data['departments'] = _get_items_from_id_list(current_user, claims=claims, id_list=data.pop('department_ids', None), orm_class=Department)

        office = Office(**data)
        office.save(current_user, claims=claims)

        return office


@blp.route('/<office_id>')
class OfficeById(MethodView):

    def get_office(self, current_user: AuthInfo, claims: List[Claim], office_id: str):
        office = Office.get(current_user, office_id, claims=claims, raise_if_not_found=True)

        return office

    @blp.response(status_code=200, schema=OfficeSchema)
    @access_required(
        'read', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def get(self, office_id):
        current_user, claims = get_current_user_with_claims()

        office = self.get_office(current_user, claims, office_id)

        return office

    @blp.arguments(schema=OfficeSchema)
    @blp.response(status_code=200, schema=OfficeSchema)
    @access_required(
        'update', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def put(self, data, office_id):
        current_user, claims = get_current_user_with_claims()
        logger.debug('Updating Office', extra={'data': data})

        office = self.get_office(current_user, claims, office_id)

        # Validate that items exist and get actual items
        data['departments'] = _get_items_from_id_list(current_user, claims=claims, id_list=data.pop('department_ids', None), orm_class=Department)

        for k, v in data.items():
            if hasattr(office, k):
                setattr(office, k, v)
            else:
                raise BadRequestException('Office has no attribute: %s' % k)
        office.save(current_user, claims=claims)
        return office

    @blp.response(status_code=204, schema=OfficeSchema)
    @access_required(
        'delete', 'offices',
        allowed_filter_fields=OFFICE_CLAIM_SPEC.filter_fields
    )
    def delete(self, office_id):
        current_user, claims = get_current_user_with_claims()

        office = self.get_office(current_user, claims, office_id)

        office.delete(current_user)
        return office
