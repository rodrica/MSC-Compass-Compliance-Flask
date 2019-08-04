import logging

from flask import current_app, request


def log_response(response):
    '''
        Log request, response status, and response content length.
        This is very similiar to `werkzeug` default logging but has the benefit that the request_id is added to the log
    '''
    level = logging.INFO
    if request.path == '/metrics':
        level = logging.DEBUG

    message = None
    if hasattr(response, 'json') and response.json:
        if 'msg' in response.json:
            message = response.json.get('msg')
        elif 'message' in response.json:
            message = response.json.get('message')

    logging.getLogger(current_app.name).log(
        level,
        "Request complete.",
        extra={
            'method': request.method,
            'path': request.full_path,
            'protocol': request.environ.get('SERVER_PROTOCOL'),
            'status': response.status,
            'status_code': response.status_code,
            'content_length': response.headers.get('Content-Length'),
            'exec_time': request.total_time,
            'payload_message': message,
            # TODO:
            # 'tenant_id': tenant_id,
            # 'user_id': user_id,
        }
    )
    return response


def register_logging(app):
    app.after_request(log_response)
