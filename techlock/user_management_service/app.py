import importlib
import logging

import flask
from flask_smorest import Blueprint

from techlock.common import ConfigManager
from techlock.common.api.flask import create_flask
from techlock.common.util.log import init_logging

from .models import ALL_CLAIM_SPECS

init_logging(flask_logger=True)
logger = logging.getLogger(__name__)

# Would love to do this via some reflection. Ran out of time for now.
routes = [
    'hydrator',
    'departments',
    'offices',
    'roles',
    'tenants',
    'users',
    'ui_data',
]

flask_wrapper = create_flask(
    "User Management",
    enable_jwt=True,
    audience='user-management',
    claim_specs=ALL_CLAIM_SPECS
)
# unwrap wrapper to ensure all plugins work properly
app = flask_wrapper.app
migrate = flask_wrapper.migrate

jwt = flask_wrapper.jwt
api = flask_wrapper.api

# Initialize ConfigManager with namespace
ConfigManager(namespace='user_management')

logger.info('Initializing routes')
for route in routes:
    logger.info('Initializing route "%s"', route)
    service = importlib.import_module("techlock.user_management_service.routes.%s" % route)
    if isinstance(service.blp, Blueprint):
        api.register_blueprint(service.blp)
    elif isinstance(service.blp, flask.Blueprint):
        app.register_blueprint(service.blp)
