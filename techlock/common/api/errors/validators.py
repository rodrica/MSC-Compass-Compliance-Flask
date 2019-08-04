import os

import pytz

from . import BadRequestException


def validate_interval(interval):
    minimum_interval = os.environ.get('MIN_INTERVAL', 300)
    if interval % minimum_interval != 0:
        raise BadRequestException('Interval must be a multiple of {} ({} min)'.format(
            minimum_interval, minimum_interval / 60))


def validate_timezone(timezone):
    try:
        pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise BadRequestException("Unknown timezone: '{}'".format(timezone))
