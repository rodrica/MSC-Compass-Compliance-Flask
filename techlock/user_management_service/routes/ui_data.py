import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint

from techlock.common.config import ConfigManager
from techlock.common.api.jwt_authorization import (
    access_required,
)

logger = logging.getLogger(__name__)

blp = Blueprint('ui_data', __name__, url_prefix='/ui-data')


@blp.route('/config')
class ConfigUrls(MethodView):

    @access_required(
        'read', 'ui_data'
    )
    def get(self):
        current_user = get_current_user()
        ensilo_url = ConfigManager().get(current_user, 'ui_config_ensio_url', raise_if_not_found=False)
        kibana_url = ConfigManager().get(current_user, 'ui_config_kibana_url', raise_if_not_found=False)

        return {"ensilo_url": ensilo_url, "kibana_url": kibana_url}
