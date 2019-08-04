import logging

from flask.views import MethodView
from flask_rest_api import Blueprint

logger = logging.getLogger(__name__)

blp = Blueprint('logout_access', __name__, url_prefix='/logout/access')


@blp.route('')
class LogoutAccess(MethodView):

    def post(self):
        pass
