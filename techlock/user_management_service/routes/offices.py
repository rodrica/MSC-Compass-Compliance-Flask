import logging
from typing import Any, Dict, List, Tuple, Union
from uuid import UUID

from flask.views import MethodView
from flask_smorest import Blueprint
from techlock.common.api import BadRequestException
from techlock.common.api.auth import access_required
from techlock.common.api.auth.claim import ClaimSet, ClaimSpec
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo
from techlock.common.orm.sqlalchemy import BaseModel

from ..models import DEPARTMENT_CLAIM_SPEC
from ..models import OFFICE_CLAIM_SPEC as claim_spec
from ..models import (
    Department,
    Office,
    OfficeListQueryParameters,
    OfficeListQueryParametersSchema,
    OfficePageableSchema,
    OfficeSchema,
)

logger = logging.getLogger(__name__)

blp = Blueprint('offices', __name__, url_prefix='/offices')

merged_claim_spec = ClaimSpec(
    resource_name=[claim_spec.resource_name, DEPARTMENT_CLAIM_SPEC.resource_name],
    filter_fields=list(set(claim_spec.filter_fields + DEPARTMENT_CLAIM_SPEC.filter_fields)),
    default_actions=list(set(claim_spec.default_actions + DEPARTMENT_CLAIM_SPEC.default_actions)),
)


def _get_items_from_id_list(
    current_user: AuthInfo,
    claims: ClaimSet,
    id_list: List[Union[str, UUID]],
    orm_class: BaseModel,
):
    if not id_list:
        return []

    items = [
        orm_class.get(current_user, entity_id=entity_id, claims=claims, raise_if_not_found=True)
        for entity_id in id_list
    ]

    return items


def _split_claims(claims: ClaimSet, *office_actions: List[str]) -> Tuple[ClaimSet, ClaimSet]:
    office_claims = ClaimSet([
        c for c in claims
        if c.action in ('*', *office_actions) and c.resource in ('*', claim_spec.resource_name)
    ])
    department_claims = ClaimSet([
        c for c in claims
        if c.action in ('*', 'read') and c.resource in ('*', DEPARTMENT_CLAIM_SPEC.resource_name)
    ])

    return office_claims, department_claims


@blp.route('')
class Offices(MethodView):

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=OfficeListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=OfficePageableSchema)
    def get(self, query_params: OfficeListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET offices')
        pageable_resp = Office.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(current_user),
            claims=claims,
        )

        return pageable_resp

    # Bit janky, but a user should only be able to add departments that it has access to, to an office.
    @access_required(required_actions=['read', 'create'], claim_spec=merged_claim_spec)
    @blp.arguments(schema=OfficeSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=OfficeSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating Office', extra={'data': data})
        office_claims, department_claims = _split_claims(claims, 'create')

        data['departments'] = _get_items_from_id_list(
            current_user,
            claims=department_claims,
            id_list=data.pop('department_ids', None),
            orm_class=Department,
        )

        office = Office(**data)
        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        office.save(current_user, claims=office_claims, commit=not dry_run)

        return office


@blp.route('/<office_id>')
class OfficeById(MethodView):

    def get_office(self, current_user: AuthInfo, claims: ClaimSet, office_id: str):
        office = Office.get(current_user, office_id, claims=claims, raise_if_not_found=True)

        return office

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=OfficeSchema)
    def get(self, office_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting office', extra={'id': office_id})
        office = self.get_office(current_user, claims, office_id)

        return office

    # Bit janky, but a user should only be able to add departments that it has access to, to an office.
    @access_required(required_actions=['read', 'update'], claim_spec=merged_claim_spec)
    @blp.arguments(schema=OfficeSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=OfficeSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, office_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating Office', extra={'data': data})
        office_claims, department_claims = _split_claims(claims, 'read', 'update')

        office = self.get_office(current_user, office_claims.filter_by_action('read'), office_id)

        # Validate that items exist and get actual items
        data['departments'] = _get_items_from_id_list(
            current_user,
            claims=department_claims,
            id_list=data.pop('department_ids', None),
            orm_class=Department,
        )

        for k, v in data.items():
            if hasattr(office, k):
                setattr(office, k, v)
            else:
                raise BadRequestException(f'Office has no attribute: {k}')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        office.save(current_user, claims=office_claims.filter_by_action('update'), commit=not dry_run)
        return office

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, office_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Deleting office', extra={'id': office_id})
        office = self.get_office(current_user, claims.filter_by_action('read'), office_id)

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        office.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)
        return
