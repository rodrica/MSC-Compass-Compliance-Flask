import importlib
import logging

import flask
from flask_rest_api import Blueprint

from techlock.common.api.flask import create_flask
from techlock.common.util.log import init_logging

init_logging(flask_logger=True)
logger = logging.getLogger(__name__)

# Would love to do this via some reflection. Ran out of time for now.
routes = [
    'authentication.token_refresh',
    'authentication.user_login',
    'authentication.user_logout_access',
    'authentication.user_logout_refresh',
    'authentication.user_registration',
    'user_management.users',
]

flask_wrapper = create_flask(__name__)
# unwrap wrapper to ensure all plugins work properly
app = flask_wrapper.app
migrate = flask_wrapper.migrate

jwt = flask_wrapper.jwt
api = flask_wrapper.api


logger.info('Initializing routes')
for route in routes:
    logger.info('Initializing route "%s"', route)
    service = importlib.import_module("techlock.auth_service.routes.%s" % route)
    if isinstance(service.blp, Blueprint):
        api.register_blueprint(service.blp)
    elif isinstance(service.blp, flask.Blueprint):
        app.register_blueprint(service.blp)


@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {
        'roles': [],
        'permissions': {
            'auth': [
                'READ_USERS',
                'CREATE_USER',
                'READ_USER',
                'UPDATE_USER',
                'DELETE_USER',
            ]
        }
    }


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.email
