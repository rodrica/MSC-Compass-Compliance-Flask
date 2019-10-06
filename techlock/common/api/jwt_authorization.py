import fnmatch
import functools
import json
import jwt
import logging
import os
from boto3.dynamodb.conditions import Attr, ConditionBase, Not
from cryptography.hazmat.primitives import serialization
from dataclasses import dataclass
from flask_jwt_extended import JWTManager
from operator import or_
from typing import Any, Dict, List, Union
from urllib.request import urlopen

from flask import current_app, g, request
from flask_jwt_extended import verify_jwt_in_request, get_raw_jwt, get_current_user
from flask_jwt_extended.exceptions import UserClaimsVerificationError
from functional import seq

from ..config import AuthInfo

logger = logging.getLogger(__name__)

tenant_header_key = 'TL-TENANT-ID'


def configure_jwt(app):
    jwt = JWTManager(app)
    jwt._user_loader_callback = user_loader
    jwt._claims_verification_callback = claims_verification_loader

    jwks_urls = os.environ.get('JWKS_URLS')
    if jwks_urls:
        jwt.rsa_keys = None

        @jwt.decode_key_loader
        def decode_key_loader(claims, headers):
            if jwt.rsa_keys and headers['kid'] in jwt.rsa_keys:
                return jwt.rsa_keys[headers['kid']]
            else:
                logger.warn('No JWT decode key found, reloading JWKS...')
                jwt.rsa_keys = load_public_keys_from_jwks_urls(jwks_urls)
                logger.debug('rsa_keys', extra={'rsa_keys': jwt.rsa_keys})

                if jwt.rsa_keys and headers['kid'] in jwt.rsa_keys:
                    return jwt.rsa_keys[headers['kid']]
                else:
                    logger.warn('No JWT decode key found after reloading.', extra={'kid': headers.get('kid')})
                    return None

    return jwt


def jwk_to_pem(jwk):
    if jwk.get('kty') == 'RSA':
        algorithm = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        return algorithm.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        ).decode()
    else:
        raise ValueError("KTY of '{}' not implemented yet".format(jwk.get('kty')))


def load_public_keys_from_jwks_urls(jwks_urls):
    rsa_keys = dict()

    for jwks_url in jwks_urls.split(','):
        json_url = urlopen(jwks_url)
        jwks = json.loads(json_url.read())

        for jwk in jwks["keys"]:
            rsa_keys[jwk['kid']] = jwk_to_pem(jwk)

    return rsa_keys


def claims_verification_loader(user_claims):
    raw_jwt = get_raw_jwt()
    return (
        'tenant_id' in raw_jwt
        and 'roles' in raw_jwt
        and 'claims' in raw_jwt
    )


def user_loader(identity) -> AuthInfo:
    raw_jwt = get_raw_jwt()
    tenant_id = raw_jwt['tenant_id']
    if tenant_header_key in request.headers:
        tenant_id = request.headers[tenant_header_key]

    return AuthInfo(
        user_id=identity,
        tenant_id=tenant_id,
    )


@dataclass
class ClaimSpec():
    actions: List[str] = None
    resource_name: str = None
    filter_fields: List[str] = None


@dataclass
class Claim():
    allow: bool
    tenant_id: str
    audience: str
    action: str
    resource: str
    id: str
    filter_field: str
    filter_value: str

    @staticmethod
    def from_string(value) -> 'Claim':
        parts = value.split(':')

        # if the claim doesn't start with 'allow' or 'deny', add 'allow'
        if parts[0].lower() not in ['allow', 'deny']:
            parts = ['allow'] + parts

        if len(parts) < 6:
            raise ValueError(
                'Claim has too few parts, expected 6 or 7, found {}. Claim = {}'.format(
                    len(parts), value
                )
            )
        if len(parts) > 7:
            raise ValueError(
                'Claim has too many parts, expected 6 or 7, found {}. Claim = {}'.format(
                    len(parts), value
                )
            )

        id = None
        filter_field = None
        filter_value = None
        if len(parts) == 6:
            id = parts[5]
        else:
            filter_field = parts[5]
            filter_value = parts[6]

        return Claim(
            allow=parts[0].lower() == 'allow',
            tenant_id=parts[1],
            audience=parts[2],
            action=parts[3].lower(),
            resource=parts[4].lower(),
            id=id,
            filter_field=filter_field,
            filter_value=filter_value
        )


def get_matching_claims(
    audience: str,
    current_user: AuthInfo,
    required_action: str,
    required_resources: List[str],
    claims_to_match: List[str],
    allowed_filter_fields: List[str] = None,
):
    '''
        Return claims that match the:
        * audience
        * tenant_id
        * required_actions
        * required_resources
        * allowed_filter_fields

        If allowed_filter_fields is None, no filters are allowed.
    '''

    claims = (
        seq(claims_to_match)
        .map(lambda x: Claim.from_string(x))
        .filter(lambda x: x.audience == audience)
        .filter(lambda x: x.tenant_id == '*' or x.tenant_id == current_user.tenant_id)
    )
    # If we shouldn't allow all actions, add action filtering
    if '*' != required_action:
        claims = claims.filter(lambda x: validate_action(x.action, required_action))

    # If we shouldn't allow all resources, add resource filtering
    if '*' not in required_resources:
        claims = claims.filter(lambda x: validate_resource(x.resource, required_resources))

    if allowed_filter_fields is None:
        claims = claims.filter(lambda x: x.filter_field is None)
    else:
        claims = claims.filter(lambda x: x.filter_field is None or x.filter_field in allowed_filter_fields)

    matching_claims = claims.to_list()
    # If there is any claim that denies access to everything, there are no matching claims.
    if any(not c.allow and c.id == '*' for c in matching_claims):
        matching_claims = list()

    return matching_claims


def validate_action(granted_action, required_action):
    return (
        granted_action == '*'
        or granted_action == required_action
        or fnmatch.fnmatch(required_action, granted_action)
    )


def validate_resource(granted_resource, required_resources):
    return (
        granted_resource == '*'
        or granted_resource in required_resources
        or any(fnmatch.fnmatch(x, granted_resource) for x in required_resources)
    )


def access_required(
    required_action: str,
    required_resources: Union[str, List[str]],
    allowed_filter_fields: List[str] = None,
):
    '''
        Validates claims, and adds all revelant claims to the Flask request.

        You can retrieve them by calling the `get_raw_jwt()`

        MUST be in a Flask request
    '''
    # do this outside of the wrapper so that it'll only be executed once, not on every invocation
    required_action = required_action.lower()
    if not isinstance(required_resources, list):
        required_resources = [required_resources]
    required_resources = [x.lower() for x in required_resources]

    def wrap(fn):
        def wrapper(*args, **kwargs):
            logger.info('headers', extra={'headers': dict(request.headers)})
            verify_jwt_in_request()

            current_user = get_current_user()
            raw_jwt = get_raw_jwt()
            if 'claims' not in raw_jwt:
                raise UserClaimsVerificationError("No 'claims' field found.")
            elif not isinstance(raw_jwt['claims'], list):
                raise UserClaimsVerificationError("Claims must be a list.")

            matching_claims = get_matching_claims(
                audience=current_app.config.get('AUDIENCE'),
                current_user=current_user,
                required_action=required_action,
                required_resources=required_resources,
                claims_to_match=raw_jwt['claims'],
                allowed_filter_fields=allowed_filter_fields,
            )

            # Add claims to flask request context
            setattr(g, 'claims', matching_claims)

            return fn(*args, **kwargs)
        return wrapper
    return wrap


def get_request_claims():
    '''Return all claims relevant to this request'''
    if hasattr(g, 'claims'):
        return getattr(g, 'claims')
    return None


def claims_to_dynamodb_condition(
    claims: List[Claim],
    id_field: str = 'entity_id',
) -> ConditionBase:
    '''
        WARNING: DynamoDB does not support wildcards.
        You MUST perform manual filtering for this yourself.

        DynamoDB does support `begins_with` and `contains`, so we'll perform those to match as closely as possible.
    '''

    allow_conditions = list()
    deny_conditions = list()

    # If we have an allow all, just filter out all denies.
    if any((c.allow and c.id == '*') for c in claims):
        for c in filter(lambda x: not x.allow, claims):
            deny_conditions.append(claim_to_dynamodb_condition(c))
    else:
        for c in claims:
            if c.allow:
                allow_conditions.append(claim_to_dynamodb_condition(c))
            else:
                deny_conditions.append(claim_to_dynamodb_condition(c))

    condition = None
    if allow_conditions:
        condition = functools.reduce(or_, filter(None.__ne__, allow_conditions))
    if deny_conditions:
        deny_condition = Not(functools.reduce(or_, filter(None.__ne__, deny_conditions)))
        if condition:
            condition &= deny_condition
        else:
            condition = deny_condition

    return condition


def claim_to_dynamodb_condition(
    claim: Claim,
    id_field: str = 'entity_id',
) -> ConditionBase:
    condition = None

    if claim.id == '*':
        # Allow all, so no condition to add.
        return None
    elif claim.id is not None:
        condition = Attr(id_field).eq(claim.id)
    elif claim.filter_field is not None:
        attr = Attr(claim.filter_field)
        value = claim.filter_value

        if value == '*':
            # Allow all, so no condition to add.
            return None
        elif '*' not in value:
            condition = attr.eq(value)
        elif value.count('*') > 1:
            # If more than 1 wildcard, we can't process it
            return None
        elif value.endswith('*'):
            # exact translation
            condition = attr.begins_with(value[:-1])
        elif value.startswith('*'):
            # not exact translation, but closest we can get
            condition = attr.contains(value[1:])
        else:
            # Wildcard is in the middle, use the largest part
            parts = value.split('*')
            condition = attr.contains(max(parts, key=len))
    else:
        # Invalid claim. Log and ignore.
        logger.warn('Invalid claim', extra={'claim': claim})

    return condition


class ClaimFilter():
    def __init__(
        self,
        claim: Claim,
        id_field: str = 'entity_id',
        false_if_deny: bool = True,
    ):
        self.claim = claim
        self.field_to_compare = claim.filter_field or id_field
        self.negate = false_if_deny and not self.claim.allow

        # If id is start, always return True
        if claim.id == '*' or claim.filter_value == '*':
            self.compare_fn = lambda value: True
        elif claim.id is not None:
            if '*' in claim.id:
                self.compare_fn = lambda value: fnmatch.fnmatch(value, claim.id)
            else:
                self.compare_fn = lambda value: value == claim.id
        elif claim.filter_value is not None:
            if '*' in claim.filter_value:
                self.compare_fn = lambda value: fnmatch.fnmatch(value, claim.filter_value)
            else:
                self.compare_fn = lambda value: value == claim.filter_value
        else:
            logger('Invalid claim', extra={'claim': claim})

    @staticmethod
    def compare_field(obj: Any, field: str, value: str):
        pass

    def __call__(self, obj: Dict[Any, Any]):
        value = self.get_value(obj, self.field_to_compare)

        if self.negate:
            return not(value is not None and self.compare_fn(value))
        else:
            return value is not None and self.compare_fn(value)


class ClassMatchesClaimFilter(ClaimFilter):
    @staticmethod
    def get_value(obj: Any, field: str):
        return getattr(obj, field, None)


class DictMatchesClaimFilter(ClaimFilter):
    @staticmethod
    def get_value(obj: Dict[Any, Any], field: str):
        return obj.get(field)


def filter_by_claims(
    objects: List[Union[Dict, Any]],
    claims: List[Claim],
    id_field: str = 'entity_id',
):
    '''
        Expects either a list of dicts, or (data)classes
        Note: It is expected that the list of claims has already be validated for action and resource.
              This does not check action or resource.
    '''
    if not objects:
        return list()

    if isinstance(objects[0], dict):
        filter_class = DictMatchesClaimFilter
    else:
        filter_class = ClassMatchesClaimFilter

    # if we have a deny all, return empty list
    if any((not c.allow and c.id == '*') for c in claims):
        return list()

    # Filter out all denies
    filtered_objects = objects
    for c in filter(lambda x: not x.allow, claims):
        filtered_objects = list(filter(filter_class(c), filtered_objects))

    # If we have an allow all, we're done
    if any((c.allow and c.id == '*') for c in claims):
        return filtered_objects

    # Otherwise, validate that everything matches the 'allow' claims
    else:
        for c in filter(lambda x: x.allow, claims):
            filtered_objects = list(filter(filter_class(c), filtered_objects))

    return filtered_objects


def can_access(
    obj: Union[Dict, Any],
    claims: List[Claim],
    id_field: str = 'entity_id',
):
    '''
        Expects either a list of dicts, or (data)classes
        Note: It is expected that the list of claims has already be validated for action and resource.
              This does not check action or resource.
    '''
    if isinstance(obj, dict):
        filter_class = DictMatchesClaimFilter
    else:
        filter_class = ClassMatchesClaimFilter

    # if we have a deny all, we don't have access
    if any((not c.allow and c.id == '*') for c in claims):
        return False

    for c in filter(lambda x: not x.allow, claims):
        if not filter_class(c)(obj):
            # deny claim matched, we don't have access
            return False

    # If we have an allow all, we have access
    if any((c.allow and c.id == '*') for c in claims):
        return True

    for c in filter(lambda x: not x.allow, claims):
        if filter_class(c)(obj):
            # allow claim matched, we have access
            return True

    # No allow claim matched, we don't have access
    return False
