import logging

from flask.views import MethodView
from flask_jwt_extended import (
    jwt_refresh_token_required, get_jwt_identity, create_access_token
)
from flask_rest_api import Blueprint

from techlock.auth_service.models import User

logger = logging.getLogger(__name__)

blp = Blueprint('token_refresh', __name__, url_prefix='/token/refresh')


@blp.route('')
class TokenRefresh(MethodView):

    @jwt_refresh_token_required
    def post(self):
        email = get_jwt_identity()
        user = User.query.filter_by(email=email).first()

        return {
            'access_token': create_access_token(identity=user)
        }, 200
