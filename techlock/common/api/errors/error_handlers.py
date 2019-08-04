import logging

from flask import jsonify

from .bad_request_exception import BadRequestException
from .conflict_exists_exception import ConflictException
from .not_found_exception import NotFoundException
from .processing_exception import ProcessingException
from .timeout_exception import TimeoutException
from .invalid_filter_exception import InvalidFilterException

_LOG = logging.getLogger('api-error-handler')


def register_error_handlers(app):
    '''
    Registers common error handlers to the app.

    Done this way because you can't have error_handlers inside blueprints. So annotations don't work.
    '''
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(500, internal_server_error)

    app.register_error_handler(NotFoundException, aegis_exception_handler)
    app.register_error_handler(ConflictException, aegis_exception_handler)
    app.register_error_handler(BadRequestException, aegis_exception_handler)
    app.register_error_handler(TimeoutException, aegis_exception_handler)
    app.register_error_handler(ProcessingException, processing_exception_handler)
    app.register_error_handler(InvalidFilterException, aegis_exception_handler)


def not_found_error(error):
    _LOG.debug(error, exc_info=True)  # Logs traceback if debug enabled

    _LOG.error('%s', error)
    return jsonify({'error': True, 'msg': 'Requested resource not found.'}), 404


def internal_server_error(error):
    _LOG.error('error_handler')
    _LOG.error('%s', error, exc_info=True)
    return jsonify({'error': True, 'msg': 'Unknown error occured on server.'}), 500


def aegis_exception_handler(error):
    _LOG.debug(error, exc_info=True)  # Logs traceback if debug enabled
    _LOG.error(error.message)

    return jsonify({'error': True, 'msg': error.message}), error.status_code


def processing_exception_handler(error):
    status = error.payload or {'status': 'processing'}
    return jsonify(status), error.status_code
