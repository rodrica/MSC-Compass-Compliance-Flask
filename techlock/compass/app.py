import logging

from environs import Env
from techlock.common import ConfigManager, init_logging
from techlock.common.api import dynamically_register_routes
from techlock.common.api.flask import create_flask

from .models import ALL_CLAIM_SPECS

Env().read_env()  # Load .env file
init_logging(flask_logger=True)
logger = logging.getLogger(__name__)

flask_wrapper = create_flask(
    "compass",
    enable_jwt=True,
    audience='compliance',
    claim_specs=ALL_CLAIM_SPECS,
)
# unwrap wrapper to ensure all plugins work properly
app = flask_wrapper.app
migrate = flask_wrapper.migrate

jwt = flask_wrapper.jwt
api = flask_wrapper.api

# Initialize ConfigManager with namespace
ConfigManager(namespace='compass')

logger.info('Initializing routes')
dynamically_register_routes(app, api)

logger.info('Ready to serve requests.')
