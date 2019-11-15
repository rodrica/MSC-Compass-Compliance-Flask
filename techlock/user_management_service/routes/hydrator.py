import logging
import os

from flask import request
from flask.views import MethodView
from flask_httpauth import HTTPBasicAuth
from flask_smorest import Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

from techlock.common.api import BadRequestException, NotFoundException
from techlock.common.api.jwt_authorization import Claim, tenant_header_key
from techlock.common.util.helper import parse_boolean
from techlock.user_management_service.models import (
    HydratorPostSchema,
    User,
)


logger = logging.getLogger(__name__)

blp = Blueprint('hydrator', __name__, url_prefix='/hydrator')
auth = HTTPBasicAuth()

AUTH_HEADER = 'Authorization'
BASIC_START = 'Basic '
basic_enabled = parse_boolean(os.environ.get('HYDRATOR_BASIC_ENABLED', 'true'))
basic_user = os.environ.get('HYDRATOR_BASIC_USER', '')
basic_password = generate_password_hash(os.environ.get('HYDRATOR_BASIC_PASSWORD', ''))

username_token_field = os.environ.get('USERNAME_TOKEN_FIELD', 'username')


@auth.verify_password
def verify_password(username, password):
    if not basic_enabled:
        return True

    if username == basic_user:
        return check_password_hash(basic_password, password)
    return False


@blp.route('')
class Hydrator(MethodView):

    @blp.arguments(HydratorPostSchema)
    @blp.response(HydratorPostSchema)
    @auth.login_required
    def post(self, data):
        audience = data.get('header').get('X-Audience')
        # Oathkeeper makes headers a list??
        if isinstance(audience, list):
            if len(audience) == 1:
                audience = audience[0]
            else:
                logger.error('Unsupported audience header', extra={'audience': audience})

        email = data.get('extra').get(username_token_field)

        if email is None:
            logger.error('No username provided', extra={'data': data})
            raise BadRequestException('No username provided')

        user = User._unsecure_get(email)
        if user is None:
            raise NotFoundException("User '{}' not found.".format(email))

        tenant_id = user.tenant_id
        if tenant_header_key in request.headers:
            tenant_id = request.headers.get(tenant_header_key)

        claims = set(filter(
            lambda x: Claim.from_string(x).tenant_id in ('*', tenant_id),
            user.claims_by_audience.get(audience)
        )) if user.claims_by_audience else set()
        role_names = set()
        for role in user.roles:
            if role.claims_by_audience:
                claims.update(filter(
                    lambda x: Claim.from_string(x).tenant_id in ('*', tenant_id),
                    role.claims_by_audience.get(audience)
                ))
                role_names.add(role.name)

        response = {
            'subject': data['subject'],
            'extra': {
                'user_id': user.entity_id,
                'tenant_id': user.tenant_id,
                'claims': list(claims),
                'roles': list(role_names)
            },
            'header': data['header']
        }

        logger.info('Hydrator data.', extra={
            'data': data,
            'request.headers': dict(request.headers),
            'response': response,
        })
        return response
