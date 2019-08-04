import json
from flask import Response

# import to expose on module level
from .logging_middleware import register_logging
from .metrics_middleware import register_metrics
from .prometheus_middleware import register_prometheus_metrics


def unsorted_jsonify(data, status=200):
    '''
        Returns a Response object with unsorted json.

        Reason for this function:
        When handling large datasets, the sorting will take far longer than the actual data retrieval.
        An example that has been observed. Data retrieval: 2.5 seconds, sorting: 40 seconds.

        One side effect is that we now won't hit HTTP caching systems because there is no garuantee that the hash will be identical.
        This shouldn't be an issues as we cache serverside. Source: https://stackoverflow.com/a/43263483/3776765

        Please use your own discretion when deciding to use this function or the standard jsonify
    '''
    return Response(
        response=json.dumps(data),
        mimetype='application/json',
        status=status
    )
