import logging
import logging.config
import os
from flask_log_request_id import RequestIDLogFilter

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        }
    },
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(process)5d] %(name)-20s %(levelname)-8s %(message)s %(attrs)s',
            '()': 'techlock.common.util.log.formatters.AttributesFormatter',
        },
        'json': {
            'format': '%(asctime)s %(process)d %(name)s %(levelname)s %(message)s %(attrs)s',
            '()': 'techlock.common.util.log.formatters.JsonAttributesFormatter',
        },
        'color': {
            'format': '[%(asctime)s] [%(process)5d] %(name)-20s %(levelname)-8s %(message)s %(attrs)s',
            '()': 'techlock.common.util.log.formatters.ColorAttributesFormatter',
        }
    },
    'filters': {
        'request_id': {
            '()': 'flask_log_request_id.RequestIDLogFilter'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
    }
}
TRUE_STRINGS = ['TRUE', 'T', 'YES', 'Y', '1']
LOG_LEVELS = ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']


def init_logging(
    config=None,
    log_level='INFO',
    flask_logger=False,
    color_format=False,
    json_format=False,
    config_port=None
):
    logging.loggers = []
    logging_config = DEFAULT_LOGGING_CONFIG.copy()

    if color_format or os.environ.get('LOG_COLOR', '').upper() in TRUE_STRINGS:
        logging_config['handlers']['console']['formatter'] = 'color'
    elif json_format or os.environ.get('LOG_JSON', '').upper() in TRUE_STRINGS:
        logging_config['handlers']['console']['formatter'] = 'json'

    log_level = (os.environ.get('LOG_LEVEL') or log_level).upper()

    assert log_level in LOG_LEVELS, "Found log level: {}. Must be one of: {}".format(log_level, LOG_LEVELS)
    logging_config['loggers']['']['level'] = log_level

    if flask_logger or os.environ.get('FLASK_LOGGER', '').upper() in TRUE_STRINGS:
        logging_config['handlers']['console']['filters'] = ['request_id']

        # Change werkzeug log level
        logging.getLogger("werkzeug").setLevel(logging.WARN)

    if config is not None:
        logging_config.update(config)

    logging.config.dictConfig(logging_config)

    config_port = (config_port or os.environ.get('LOG_CONFIG_PORT'))
    if config_port:
        log_server_thread = logging.config.listen(port=config_port)
        log_server_thread.start()
