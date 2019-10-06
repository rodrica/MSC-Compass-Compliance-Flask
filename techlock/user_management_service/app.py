import importlib
import logging

import flask
from flask_smorest import Blueprint

from techlock.common.api.flask import create_flask
from techlock.common.util.log import init_logging

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
]

flask_wrapper = create_flask(__name__, enable_jwt=True, audience='user-management')
# unwrap wrapper to ensure all plugins work properly
app = flask_wrapper.app
migrate = flask_wrapper.migrate

jwt = flask_wrapper.jwt
api = flask_wrapper.api


logger.info('Initializing routes')
for route in routes:
    logger.info('Initializing route "%s"', route)
    service = importlib.import_module("techlock.user_management_service.routes.%s" % route)
    if isinstance(service.blp, Blueprint):
        api.register_blueprint(service.blp)
    elif isinstance(service.blp, flask.Blueprint):
        app.register_blueprint(service.blp)


# @jwt.user_identity_loader
# def user_identity_lookup(user):
#     return user.email
