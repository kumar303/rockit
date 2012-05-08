import functools

from django import http
from django.conf import settings

import commonware.log
import jwt


log = commonware.log.getLogger('music')


def require_api_key(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kw):
        raw_sig_request = request.GET.get('r') or request.POST.get('r')
        if not raw_sig_request:
            return http.HttpResponseBadRequest('r was not in request')
        raw_sig_request = str(raw_sig_request)
        allowed = False
        try:
            sig_request = jwt.decode(raw_sig_request, verify=False)
        except jwt.DecodeError:
            log.exception('signed request was invalid')
        client_key = settings.API_CLIENTS.get(sig_request['iss'])
        if not client_key:
            return http.HttpResponseBadRequest()
        try:
            jwt.decode(raw_sig_request, client_key, verify=True)
            allowed = True
        except jwt.DecodeError:
            log.exception('signed request for %s was invalid')
        if not allowed:
            return http.HttpResponseForbidden()
        return view(request, raw_sig_request, sig_request, *args, **kw)
    return wrapper
