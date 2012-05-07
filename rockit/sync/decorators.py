import functools
import json

from django import http
from django.shortcuts import get_object_or_404

import commonware.log
import jwt

from rockit.music.models import VerifiedEmail


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


def json_view(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        response = f(request, *args, **kw)
        if hasattr(response, 'status_code') and response.status_code != 200:
            return response
        return http.HttpResponse(json.dumps(response),
                                 content_type='application/json')
    return wrapper


def require_upload_key(view):
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
        else:
            user_email = sig_request['iss']
            em = get_object_or_404(VerifiedEmail, email=user_email)
            if em.upload_key:
                try:
                    jwt.decode(raw_sig_request, em.upload_key, verify=True)
                    allowed = True
                except jwt.DecodeError:
                    log.exception('signed request for %s was invalid'
                                  % user_email)
            else:
                log.info('no upload_key for %s' % user_email)
        if not allowed:
            return http.HttpResponseForbidden()
        return view(request, raw_sig_request, sig_request, *args, **kw)
    return wrapper
