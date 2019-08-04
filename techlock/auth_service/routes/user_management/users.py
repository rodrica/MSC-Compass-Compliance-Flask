import logging

from flask.views import MethodView
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt_claims
)
from flask_rest_api import Blueprint

logger = logging.getLogger(__name__)

blp = Blueprint('users', __name__, url_prefix='/users')


@blp.route('')
class Users(MethodView):

    @jwt_required
    def get(self):
        claims = get_jwt_claims()
        current_user = get_jwt_identity()

        return {
            'claims': claims,
            'current_user': current_user,
        }


@blp.route('/<user_id>')
class User(MethodView):

    @jwt_required
    def get(self):
        pass

    @jwt_required
    def put(self):
        pass

    @jwt_required
    def delete(self):
        pass
