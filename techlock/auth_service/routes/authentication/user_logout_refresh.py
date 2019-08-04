import logging

from flask.views import MethodView
from flask_rest_api import Blueprint

logger = logging.getLogger(__name__)

blp = Blueprint('logout_refresh', __name__, url_prefix='/logout/refresh')


@blp.route('')
class LogoutRefresh(MethodView):

    def post(self):
        pass
