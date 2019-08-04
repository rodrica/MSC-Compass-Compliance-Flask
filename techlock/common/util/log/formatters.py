import logging
import coloredlogs
import json
import datetime

from pythonjsonlogger.jsonlogger import JsonFormatter


BUILT_IN_ATTRIBUTES = [
    'relativeCreated', 'process', 'module', 'funcName', 'message', 'filename', 'levelno',
    'processName', 'lineno', 'asctime', 'msg', 'args', 'exc_text', 'name',
    'thread', 'created', 'threadName', 'msecs', 'pathname', 'exc_info', 'levelname', 'stack_info'
]


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


class AttributesFormatter(logging.Formatter):
    def format(self, record):
        attributes = {key: value for (key, value) in record.__dict__.items() if key not in BUILT_IN_ATTRIBUTES}

        record.__dict__['attrs'] = json.dumps(attributes, default=default)

        message = super(AttributesFormatter, self).format(record)

        return message


class JsonAttributesFormatter(JsonFormatter):
    def format(self, record):
        attributes = {key: value for (key, value) in record.__dict__.items() if key not in BUILT_IN_ATTRIBUTES}

        for key in attributes.keys():
            del record.__dict__[key]

        record.__dict__['attrs'] = attributes

        message = super(JsonAttributesFormatter, self).format(record)

        return message


class ColorAttributesFormatter(coloredlogs.ColoredFormatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super(ColorAttributesFormatter, self).__init__(
            fmt=fmt, datefmt=datefmt, style=style,
            field_styles=dict(coloredlogs.DEFAULT_FIELD_STYLES, **{'attrs': {'color': 'cyan'}}),
            level_styles=dict(coloredlogs.DEFAULT_LEVEL_STYLES, **{
                'info': {'color': 'green'},
                'debug': {'color': 'blue'}
            })
        )

    def format(self, record):
        attributes = {key: value for (key, value) in record.__dict__.items() if key not in BUILT_IN_ATTRIBUTES}
        record.__dict__['attrs'] = attributes

        message = super(ColorAttributesFormatter, self).format(record)

        return message
