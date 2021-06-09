import logging

from flask.views import MethodView
from flask_jwt_extended import get_current_user
from flask_smorest import Blueprint
from techlock.common.api.auth import access_required
from techlock.common.config import ConfigManager

from ..models import DashboardDataSchema

logger = logging.getLogger(__name__)

blp = Blueprint('ui_data', __name__, url_prefix='/ui-data')


@blp.route('/config')
class ConfigUrls(MethodView):

    @access_required(
        'read', 'ui_data',
    )
    def get(self):
        current_user = get_current_user()
        cm = ConfigManager()
        ensilo_url = cm.get(current_user, 'ui_config.ensilo_url')
        kibana_url = cm.get(current_user, 'ui_config.kibana_url')
        kenna_url = cm.get(current_user, 'ui_config.kenna_url')
        superadmin_kenna_url = cm.get(current_user, 'ui_config.superadmin_kenna_url')
        feature_flags = cm.get(current_user, 'ui_config.feature_flags', default=dict())
        dashboard_data = DashboardDataSchema(many=True).load(cm.get(current_user, 'ui_config.dashboard', list()))
        vigitrust_url = cm.get(current_user, 'ui_config.vigitrust_url')

        return {
            "ensilo_url": ensilo_url,
            "kibana_url": kibana_url,
            "kenna_url": kenna_url,
            "superadmin_kenna_url": superadmin_kenna_url,
            "feature_flags": feature_flags,
            "dashboard_data": dashboard_data,
            "vigitrust_url": vigitrust_url,
        }
