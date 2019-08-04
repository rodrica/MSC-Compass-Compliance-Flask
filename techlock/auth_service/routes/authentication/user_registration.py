import logging

from flask.views import MethodView
from flask_rest_api import Blueprint

from techlock.common.api.models import ErrorResponse
from techlock.common.orm.sqlalchemy.db import db
from techlock.auth_service.models import (
    RegistrationResponse, RegistrationSchema, RegistrationResponseSchema,
    User,
)

logger = logging.getLogger(__name__)

blp = Blueprint('registration', __name__, url_prefix='/registration')


@blp.route('')
class UserRegistration(MethodView):

    @blp.arguments(RegistrationSchema, location='json', as_kwargs=True)
    @blp.response(RegistrationResponseSchema, code=201)
    def post(self, **kwargs):
        user = User.query.filter_by(email=kwargs['email']).first()

        if not user:
            try:
                user = User(**kwargs)
                # insert the user
                db.session.add(user)
                db.session.commit()

                return RegistrationResponse(
                    message='User {} was created'.format(user.email),
                )
            except Exception as e:
                logger.exception('Failed to create user.')
                return ErrorResponse(
                    message='Failed to create user',
                    error=str(e),
                )
        else:
            logger.warning('User already exists.')
            return ErrorResponse(
                message='User already exists.',
                error='User already exists.',
            )
