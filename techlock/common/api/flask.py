import logging
import os

from dataclasses import dataclass, is_dataclass, asdict
from decimal import Decimal
from flask import Flask, json as flask_json
from flask_cors import CORS
from flask_compress import Compress
from flask_log_request_id import RequestID
from flask_migrate import Migrate
from flask_smorest import Api
from typing import Any

from techlock.common.api.errors import register_error_handlers
from techlock.common.api.middleware import (
    register_logging, register_metrics, register_prometheus_metrics
)
from techlock.common.api.jwt_authorization import configure_jwt
from techlock.common.orm.sqlalchemy.db import db, init_db
from techlock.common.util.helper import parse_boolean


logger = logging.getLogger(__name__)

# TODO: load from config file or env
default_flask_config = {
    'OPENAPI_VERSION': '3.0.2',
    'OPENAPI_URL_PREFIX': '/doc',
    'OPENAPI_JSON_PATH': '/openapi.json',
    'OPENAPI_SWAGGER_UI_PATH': '/swagger',
    'OPENAPI_SWAGGER_UI_VERSION': '3.22.1',
    'OPENAPI_REDOC_PATH': '/redoc',
    'OPENAPI_REDOC_URL': 'https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.min.js',

    'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:password@192.168.10.10:5432/user_management_service',

    'JWT_ALGORITHM': 'RS256',
    'JWT_IDENTITY_CLAIM': 'sub',
    'JWT_USER_CLAIMS': 'claims'
}


class FlaskJSONEncoder(flask_json.JSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'

    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.hex()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif is_dataclass(obj):
            return asdict(obj)
        return flask_json.JSONEncoder.default(self, obj)


@dataclass
class FlaskWrapper():
    app: Any
    api: Any
    jwt: Any
    migrate: Any


def create_flask(
    import_name,
    enable_jwt=True,
    audience=None,
):
    '''
        Creates a Flask app and sets it up. This means:
        1. Register `request_context` to allow per request psql_connections
        2. Register error handlers for all exceptions in `techlock.common.api.errors`, 404, and 500 errors
        3. Register the app so that the request_id is populated per request. (enhanced logging)
        4. Register an after_request function that will log request, and response data.

        Returns:
            FlaskWrapper
    '''
    app = Flask(import_name)
    if audience:
        app.config['AUDIENCE'] = audience
    app.config.update(default_flask_config)
    app.config.update({k[6:]: v for k, v in os.environ.items() if k.startswith('FLASK_')})

    CORS(app)
    RequestID(app)
    register_error_handlers(app)

    # Order matters! We want metrics to compute the total time before we log it and add it to prometheus metrics
    Compress(app)
    register_logging(app)
    register_prometheus_metrics(app)
    register_metrics(app)

    app.json_encoder = FlaskJSONEncoder
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    # # Add custom converters
    # app.url_map.converters['unicode_unquote'] = UnicodeUnquoteConverter
    # app.url_map.converters['default'] = UnicodeUnquoteConverter

    init_db(db)
    db.init_app(app)
    migrate = Migrate(app, db)

    jwt = None
    if enable_jwt or parse_boolean(os.environ.get('JWT_ENABLED')):
        logger.info('Enabling JWT.')
        jwt = configure_jwt(app)

    api = Api(app)

    return FlaskWrapper(
        app,
        api,
        jwt,
        migrate
    )
