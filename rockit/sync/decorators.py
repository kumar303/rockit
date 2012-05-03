import functools
import json

from django import http

import commonware.log

log = commonware.log.getLogger('playdoh')


def post_required(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        if request.method != 'POST':
            return http.HttpResponseNotAllowed(['POST'])
        else:
            return f(request, *args, **kw)
    return wrapper


def log_exception(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        try:
            return f(request, *args, **kw)
        except:
            log.exception('in request')
            raise
    return wrapper


def remote_jsonp_view(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        response = f(request, *args, **kw)
        if hasattr(response, 'status_code') and response.status_code != 200:
            return response
        callback = request.GET.get('callback', 'callback')

        return http.HttpResponse('%s' % (json.dumps(response)),
                                 content_type='application/javascript')
        #return http.HttpResponse('%s(%s)' % (callback, json.dumps(response)),
        #                         content_type='application/javascript')
    return wrapper
