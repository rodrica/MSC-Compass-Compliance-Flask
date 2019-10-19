import logging

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint

from techlock.common.api import BadRequestException, NotFoundException
from techlock.common.api.jwt_authorization import Claim, tenant_header_key
from techlock.common.config import AuthInfo
from techlock.user_management_service.models import (
    HydratorPostSchema,
    User,
    Role
)

logger = logging.getLogger(__name__)

blp = Blueprint('hydrator', __name__, url_prefix='/hydrator')


@blp.route('')
class Hydrator(MethodView):

    @blp.arguments(HydratorPostSchema)
    @blp.response(HydratorPostSchema)
    def post(self, data):
        audience = request.headers.get('X-Audience')
        # Oathkeeper makes headers a list??
        if isinstance(audience, list):
            if len(audience) == 1:
                audience = audience[0]
            else:
                logger.error('Unsupported audience header', extra={'audience': audience})

        email = data.get('extra').get('username')

        if email is None:
            logger.error('No username provided', extra={'data': data})
            raise BadRequestException('No username provided')

        user = User._unsecure_get(email)
        if user is None:
            raise NotFoundException("User '{}' not found.".format(email))

        tenant_id = user.tenant_id
        if tenant_header_key in request.headers:
            tenant_id = request.headers.get(tenant_header_key)

        current_user = AuthInfo(user_id=user.email, tenant_id=user.tenant_id)
        roles = Role.get_all(
            current_user,
            ids=user.role_ids,
            claims=[Claim.from_string('{}:*:*:roles:*'.format(user.tenant_id))]
        )

        users_claims = user.claims_by_audience.get(audience)
        claims = set(users_claims) if users_claims else set()
        role_names = set()
        for role in roles.items:
            claims.update(filter(
                lambda x: Claim.from_string(x).tenant_id == tenant_id,
                role.claims_by_audience.get(audience)
            ))
            role_names.add(role.name)

        response = {
            'subject': email,
            'extra': {
                'tenant_id': user.tenant_id,
                'claims': list(claims),
                'roles': list(role_names)
            },
            'header': data['header']
        }

        logger.info('args', extra={
            'args2': data,
            'request.headers': request.headers,
            'response': response,
        })
        return response
