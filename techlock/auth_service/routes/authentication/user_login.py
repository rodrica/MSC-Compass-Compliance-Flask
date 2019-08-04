import bcrypt
import logging

from flask.views import MethodView
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_rest_api import Blueprint

from techlock.auth_service.models import (
    LoginSchema, User
)

logger = logging.getLogger(__name__)

blp = Blueprint('login', __name__, url_prefix='/login')


@blp.route('')
class UserLogin(MethodView):

    @blp.arguments(LoginSchema, location='json', as_kwargs=True)
    def post(self, email, password, **kwargs):
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            # Generate tokens
            access_token = create_access_token(identity=user)
            refresh_token = create_refresh_token(identity=user)

            return {
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 200
        else:
            return {
                'message': 'Login failed.'
            }, 401
