import logging
import os

from flask import Response, current_app, request
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest, multiprocess

_LOG = logging.getLogger('promethreus-middleware')

REQUEST_COUNT = Counter(
    'request_count',
    'App Request Count',
    ['app_name', 'method', 'endpoint', 'full_path', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency',
    ['app_name', 'endpoint']
)
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')


def update_metrics(response):
    # Don't collect metrics for the metrics endpoint itself
    try:
        if request.path != "/metrics":
            if hasattr(request, "total_time"):
                REQUEST_LATENCY.labels(current_app.name, request.path).observe(request.total_time)
            REQUEST_COUNT.labels(
                current_app.name,
                request.method,
                request.path,
                request.full_path,
                str(response.status_code),
            ).inc()
    except Exception as e:
        _LOG.exception(e)

    return response


def metrics_api_single_process():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


def metrics_api_multi_process():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


def register_prometheus_metrics(app):
    app.after_request(update_metrics)

    api = metrics_api_single_process
    if 'prometheus_multiproc_dir' in os.environ:
        api = metrics_api_multi_process

    app.add_url_rule('/metrics', 'metrics', api)
