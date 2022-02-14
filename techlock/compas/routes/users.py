import logging
from dataclasses import asdict
from typing import Any, Dict, List, Tuple, Union
from uuid import UUID

from flask_smorest import Blueprint
from sqlalchemy import and_ as sql_and_  # diffentiate from operators.and_
from techlock.common.api import BadRequestException, ConflictException
from techlock.common.api.auth import Claim, access_required
from techlock.common.api.auth.claim import ClaimSet, ClaimSpec
from techlock.common.api.auth.utils import SYSTEM_TENANT_ID
from techlock.common.api.models.dry_run import DryRunSchema
from techlock.common.config import AuthInfo, ConfigManager
from techlock.common.messaging.sns import Envelope
from techlock.common.messaging.sns import publish as publish_sns
from techlock.common.orm.sqlalchemy import BaseModel
from techlock.common.util.helper import suppress_with_log

from flask.views import MethodView

from ..models import ROLE_CLAIM_SPEC
from ..models import USER_CLAIM_SPEC as claim_spec
from ..models import (
    PostUserChangePasswordSchema,
    Role,
    UpdateUserSchema,
    User,
    UserListQueryParameters,
    UserListQueryParametersSchema,
    UserPageableSchema,
    UserSchema,
)
from ..services import get_idp

logger = logging.getLogger(__name__)

blp = Blueprint('users', __name__, url_prefix='/users')

idp_attribute_keys = []

merged_claim_spec = ClaimSpec(
    resource_name=[
        claim_spec.resource_name,
        ROLE_CLAIM_SPEC.resource_name,
    ],
    filter_fields=list(
        set(
            claim_spec.filter_fields
            + ROLE_CLAIM_SPEC.filter_fields,  # noqa: C812
        ),
    ),
    default_actions=list(
        set(
            claim_spec.default_actions
            + ROLE_CLAIM_SPEC.default_actions,  # noqa: C812
        ),
    ),
)


def _get_items_from_id_list(
    current_user: AuthInfo,
    claims: List[Claim],
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


def _get_user(current_user: AuthInfo, claims: ClaimSet, user_id: str) -> User:
    if not claims:
        # if no claims, add one that allows the user to see himself
        claims = [Claim(True, current_user.tenant_id, '*', '*', 'users', id=current_user.user_id, filter_field=None, filter_value=None)]

    user = User.get(current_user, user_id, claims=claims, raise_if_not_found=True)

    return user


def _is_ftp_username_unique(current_user: AuthInfo, ftp_username: str):
    ftp_user_count = User.query.filter(
        sql_and_(
            User.is_active.is_(True),
            User.ftp_username == ftp_username,
        ),
    ).count()
    logger.debug(f'ftp_user_count: {ftp_user_count}')

    return ftp_user_count == 0


def set_claims_default_tenant(data: dict, default_tenant_id: UUID):
    claims_by_audience = data.get('claims_by_audience')
    if claims_by_audience is not None:
        for key, claims in claims_by_audience.items():
            new_claims = []
            for claim in claims:
                c = Claim.from_string(claim)
                if c.tenant_id == '':
                    c = Claim(**{**asdict(c), 'tenant_id': default_tenant_id})
                new_claims = new_claims + [str(c)]
            claims_by_audience[key] = new_claims
    return claims_by_audience


def _split_claims(claims: ClaimSet, *office_actions: List[str]) -> Tuple[ClaimSet, ClaimSet]:
    user_claims = ClaimSet([
        c for c in claims
        if c.action in ('*', *office_actions) and c.resource in ('*', claim_spec.resource_name)
    ])
    role_claims = ClaimSet([
        c for c in claims
        if c.action in ('*', 'read') and c.resource in ('*', ROLE_CLAIM_SPEC.resource_name)
    ])

    return user_claims, role_claims


@blp.route('')
class Users(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @access_required('read', claim_spec=claim_spec)
    @blp.arguments(schema=UserListQueryParametersSchema, location='query')
    @blp.response(status_code=200, schema=UserPageableSchema)
    def get(self, query_params: UserListQueryParameters, current_user: AuthInfo, claims: ClaimSet):
        logger.info('GET users')
        if not claims:
            # if no claims, add one that allows the user to see himself
            claims = [Claim(True, current_user.tenant_id, '*', '*', 'users', id=current_user.user_id, filter_field=None, filter_value=None)]

        pageable_resp = User.get_all(
            current_user,
            offset=query_params.offset,
            limit=query_params.limit,
            sort=query_params.sort,
            additional_filters=query_params.get_filters(current_user),
            claims=claims,
        )

        return pageable_resp

    @access_required(['read', 'create'], claim_spec=merged_claim_spec)
    @blp.arguments(schema=UpdateUserSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=201, schema=UserSchema)
    def post(self, data: Dict[str, Any], dry_run: bool, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Creating user', extra={'data': data})
        if current_user.tenant_id == SYSTEM_TENANT_ID:
            raise BadRequestException('Can not create system users.')

        # Since users are to be unique across all tenants by email address, we must
        # get the full list of users, even ones from other tenants. Therefore we use
        # _unsecure_get() to get a list of users, even ones the requesting user does not
        # have authorization to see.
        user = User._unsecure_get(data['email'])
        if user is not None:
            raise ConflictException('User with email = {} already exists.'.format(data['email']))

        ftp_username = data.get('ftp_username')
        if ftp_username == '':
            ftp_username = None
        if ftp_username and not _is_ftp_username_unique(current_user, ftp_username):
            # Validate that ftp_username is unique to the tenant
            raise ConflictException(f"ftp_username '{ftp_username}' already exists.")

        user_claims, department_claims, office_claims, role_claims = _split_claims(claims, 'create')
        # Validate that items exist and get actual items
        roles = _get_items_from_id_list(current_user, claims=role_claims, id_list=data.get('role_ids'), orm_class=Role)

        user = User(
            entity_id=data.get('email'),
            email=data.get('email'),
            name=data.get('name'),
            family_name=data.get('family_name'),
            ftp_username=ftp_username,
            description=data.get('description'),
            tags=data.get('tags'),
            roles=roles,
        )

        if dry_run:
            logger.info('Dry run, creating user')
            # Save so that the created_by fields get set
            user.save(current_user, claims=user_claims, commit=False)
        else:
            logger.info('Adding user to idp')
            idp_attributes = {k: v for k, v in data.items() if k in idp_attribute_keys}

            self.idp.create_user(
                current_user,
                user,
                idp_attributes=idp_attributes,
            )

            try:
                self.idp.update_user_roles(current_user, user, user.roles)

                logger.info('User added to idp, storing internally')
                user.save(current_user, claims=user_claims)
                logger.info('User created')
            except Exception:
                # Clean up silently. We expect part of this to fail, because if everything was created properly, we wouldn't be here.
                # IDP user was created successfully, so if it failed to delete, we're in trouble
                with suppress_with_log(logger, Exception, log_level=logging.ERROR):
                    self.idp.delete_user(current_user, user)

                with suppress_with_log(logger, Exception, log_level=logging.WARNING):
                    user = _get_user(current_user, data['email'])
                    user.delete(current_user, claims=user_claims)

                raise

        return user


@blp.route('/<user_id>')
class UserById(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @access_required('read', claim_spec=claim_spec)
    @blp.response(status_code=200, schema=UserSchema)
    def get(self, user_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.info('Getting user', extra={'id': user_id})
        user = _get_user(current_user, claims, user_id)

        return user

    @access_required(['read', 'update'], claim_spec=merged_claim_spec)
    @blp.arguments(schema=UpdateUserSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200, schema=UserSchema)
    def put(self, data: Dict[str, Any], dry_run: bool, user_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Updating user', extra={'data': data})
        user_claims, department_claims, office_claims, role_claims = _split_claims(claims, 'create')

        # User.validate(data, validate_required_fields=False)
        user = _get_user(current_user, user_claims.filter_by_action('read'), user_id)

        if user.email != data.get('email'):
            raise BadRequestException('Email can not be changed.')

        # Validate that items exist and get actual items
        data['roles'] = _get_items_from_id_list(current_user, claims=role_claims, id_list=data.pop('role_ids', None), orm_class=Role)

        ftp_username = data.get('ftp_username')
        if ftp_username == '':
            ftp_username = None
        if ftp_username and ftp_username != user.ftp_username and not _is_ftp_username_unique(current_user, ftp_username):
            # Validate that ftp_username is unique to the tenant
            raise ConflictException(f"ftp_username '{ftp_username}' already exists.")

        attributes_to_update = {}
        for k, v in data.items():
            if k in idp_attribute_keys:
                attributes_to_update[k] = v
            elif hasattr(user, k):
                setattr(user, k, v)
                if k in ('name', 'family_name'):
                    attributes_to_update[k] = v
            else:
                raise BadRequestException(f'User has no attribute: {k}')

        user.save(current_user, claims=user_claims.filter_by_action('update'), commit=not dry_run)

        if not dry_run:
            self.idp.update_user_attributes(current_user, user, attributes_to_update)
            self.idp.update_user_roles(current_user, user, data['roles'])

        return user

    @access_required(['read', 'delete'], claim_spec=claim_spec)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=204)
    def delete(self, dry_run: bool, user_id: str, current_user: AuthInfo, claims: ClaimSet):
        if current_user.user_id == user_id:
            return BadRequestException('Can not delete yourself.')

        user = _get_user(current_user, claims.filter_by_action('read'), user_id)

        if not dry_run:
            self.idp.delete_user(current_user, user)
            logger.info('Deleted user from userpool')

        # no need to rollback on dry-run, flask-sqlalchemy does this for us.
        user.delete(current_user, claims=claims.filter_by_action('delete'), commit=not dry_run)
        logger.info('Deleted user', extra={'user': user.entity_id})

        return


@blp.route('/<user_id>/change_password')
class UserChangePassword(MethodView):

    def __init__(self, *args, **kwargs):
        MethodView.__init__(self, *args, **kwargs)
        self.idp = get_idp()

    @blp.arguments(schema=PostUserChangePasswordSchema)
    @blp.arguments(DryRunSchema, location='query', as_kwargs=True)
    @blp.response(status_code=200)
    @access_required(
        'update', 'user_passwords',
        allowed_filter_fields=claim_spec.filter_fields,
    )
    def post(self, data: dict, dry_run: bool, user_id: str, current_user: AuthInfo, claims: ClaimSet):
        logger.debug('Changing password for user')
        user = _get_user(current_user, claims, user_id)

        if not dry_run:
            self.idp.change_password(current_user, user, data.get('new_password'))

        cm = ConfigManager()
        # Password was successfully changed, log any errors that occur in the post processing
        # But don't raise it, we need to prevent the request itself from returning an error code.
        with suppress_with_log(logger):
            publish_sns(
                Envelope(
                    topic_arn=cm.get('sns.topics.UserNotification'),
                    subject='Password Changed',
                    message={
                        'user_id': user_id,
                        'changed_by': current_user.user_id,
                        'dry_run': dry_run,
                    },
                    tenant_id=current_user.tenant_id,
                    source='user-management-service',
                    severity='INFO',
                ),
            )
