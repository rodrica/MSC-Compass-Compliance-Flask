
import logging
import ntpath
import numbers
import posixpath
import re
import timeit

from contextlib import contextmanager
from datetime import timedelta
from types import LambdaType


def basename(s):
    '''
        Return the basename os independently
        If you use os.path.basename, then you can only get the basename if the path is a host OS path.
        i.e.: If you run this on Windows, you can't get the basename of a unix path,
              and on Unix you can't get the basename of a Windows path.
    '''
    if ntpath.sep in s:
        return ntpath.basename(s)
    else:
        return posixpath.basename(s)


def try_parse(value, try_type, default=None):
    '''
        ARGS:
            value: Value to parse
            try_type: Type to try to parse as, can be a single value, or a list of types to try.
            default: Can be a value or a lambda. If lambda, it will be passed the value only. This allows chaining of `try_parse`.

        e.g.:
        `try_parse('3.3', (int, float))
        `try_parse('3.3', int, default=lambda x: try_parse(x, float))`
    '''
    try:
        # If list, tuple, or set. Loop through all entries and try to parse.
        if isinstance(try_type, list) or isinstance(try_type, tuple) or isinstance(try_type, set):
            for t in try_type:
                try:
                    return t(value)
                except Exception:
                    pass
        else:
            return try_type(value)
    except Exception:
        pass

    # Couldn't parse as any of the provided types, falling back to default.
    if isinstance(default, LambdaType):
        return default(value)
    else:
        return default


def parse_boolean(input_string, handle_numeric=False):
    _true_strings = ['t', 'true', 'y', 'yes']
    try:
        if isinstance(input_string, str):
            if handle_numeric:
                return input_string.lower() in _true_strings or try_parse(input_string.lower(), int, 0) > 0
            else:
                return input_string.lower() in _true_strings
        elif isinstance(input_string, numbers.Number) and handle_numeric:
            return input_string > 0
        else:
            return False
    except Exception as e:
        raise ValueError(e.message)


def minify_string(s, minify_comma=False):
    minified_str = re.sub(r'[\s]+', ' ', s) \
        .replace('( ', '(') \
        .replace(' )', ')') \
        .strip()

    if minify_comma:
        minified_str = minified_str.replace(', ', ',')

    return minified_str


def floor_to_interval(value, floor_to):
    return value // floor_to * floor_to


def to_human_time(days=0, hours=0, minutes=0, seconds=0, milliseconds=0):
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    if delta.days != 0:
        template = '{days} days, {hours:02d}:{minutes:02d}:{seconds:02d} hours'
    elif delta.seconds > 3600:
        template = '{hours}:{minutes:02d}:{seconds:02d} hours'
    elif delta.seconds > 60:
        template = '{minutes}:{seconds:02d}.{milliseconds:3.0f} minutes'
    else:
        template = '{seconds}.{milliseconds:3.0f} seconds'

    return template.format(
        days=delta.days,
        hours=delta.seconds // 3600,
        minutes=delta.seconds // 60 % 60,
        seconds=delta.seconds % 60,
        milliseconds=delta.microseconds / 1000
    )


def to_human_bytes(tbytes=0, gbytes=0, mbytes=0, kbytes=0, bytes=0, long_format=False, detailed=False, precision=2):
    # To bytes
    total_bytes = bytes + (kbytes << 10) + (mbytes << 20) + (gbytes << 30) + (tbytes << 40)

    groups = list()
    for x in range(4, -1, -1):
        _bytes = total_bytes >> (x * 10)
        total_bytes -= _bytes << (x * 10)
        groups.append(_bytes)

    human_str = ''
    precision_used = 0
    append_str = ''
    if groups[0] > 0:
        human_str += '{}'.format(groups[0])
        suffix = 'Tebibytes' if long_format else 'Tb'
        if detailed:
            human_str += ' ' + suffix + ' '
        else:
            human_str += '.'
            append_str = suffix
        precision_used += 1
    if groups[1] > 0 and precision_used < precision:
        human_str += '{}'.format(groups[1])
        suffix = 'Gibibytes' if long_format else 'Gb'
        if detailed:
            human_str += ' ' + suffix + ' '
        elif precision_used == 0:
            human_str += '.'
            append_str = suffix
        precision_used += 1
    if groups[2] > 0 and precision_used < precision:
        human_str += '{}'.format(groups[2])
        suffix = 'Mebibytes' if long_format else 'Mb'
        if detailed:
            human_str += ' ' + suffix + ' '
        elif precision_used == 0:
            human_str += '.'
            append_str = suffix
        precision_used += 1
    if groups[3] > 0 and precision_used < precision:
        human_str += '{}'.format(groups[3])
        suffix = 'Kibibytes' if long_format else 'Kb'
        if detailed:
            human_str += ' ' + suffix + ' '
        elif precision_used == 0:
            human_str += '.'
            append_str = suffix
        precision_used += 1
    if groups[4] > 0 and precision_used < precision:
        human_str += '{}'.format(groups[4])
        suffix = 'bytes' if long_format else 'b'
        if detailed:
            human_str += ' ' + suffix + ' '
        elif precision_used == 0:
            append_str = suffix

    human_str = human_str.rstrip('.') + ' ' + append_str
    return human_str.strip()


@contextmanager
def supress(*exceptions):
    try:
        yield
    except exceptions:
        pass


@contextmanager
def supress_with_log(log_level, logger, *exceptions):
    try:
        yield
    except exceptions as e:
        logger.log(log_level, e.message, exc_info=True)


@contextmanager
def log_execution_time(logger, log_level=logging.INFO, message="Execution took: %(exec_time).3f seconds"):
    '''
        Simply tracks and logs the execution time of a given block of code.

        How to use:
            with log_execution_time(logging.INFO, _LOG):
                <your_code>

        Args:
            log_level:  The level to log to, e.g.: logging.DEBUG, logging.INFO, logging.WARN, logging.ERROR
            logger:     The logger to log to.
            message:    The string message to log, the execution time will be added by standard string formatting as the parameter `exec_time`
    '''
    start_time = timeit.default_timer()
    yield
    execution_time = timeit.default_timer() - start_time

    logger.log(
        log_level,
        message,
        exec_time=execution_time,
        human_time=to_human_time(seconds=execution_time)
    )
