import time

from flask import request


def start_timer():
    request.start_time = time.time()


def stop_timer(response):
    # time in milliseconds
    request.total_time = int(round((time.time() - request.start_time) * 1000))

    return response


def register_metrics(app):
    app.before_request(start_timer)
    app.after_request(stop_timer)
