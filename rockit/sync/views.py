import hashlib
import os
import uuid

from django.conf import settings
from django import http
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import commonware.log

from rockit.music.models import Track, TrackFile, VerifiedEmail
from . import tasks
from .decorators import (post_required, log_exception,
                         json_view, require_upload_key)

log = commonware.log.getLogger('rockit')


def index(request):
    return http.HttpResponse('sync server!')


@json_view
def songs(request):
    email = get_object_or_404(VerifiedEmail, email=request.GET.get('email'))
    af = (Track.objects.filter(email=email)
                       .exclude(files=None)
                       .order_by('-created'))
    ob = []
    for afile in af.all():
        ob.append(afile.to_json())
    return {'songs': ob}


@post_required
@csrf_exempt
@log_exception
@require_upload_key
def upload(request, raw_sig_request, sig_request):
    if not os.path.exists(settings.UPLOAD_TEMP_DIR):
        log.info('creating upload temp dir')
        os.makedirs(settings.UPLOAD_TEMP_DIR)
    key, file = request.FILES.items()[0]
    _, ext = os.path.splitext(key)
    path = os.path.join(settings.UPLOAD_TEMP_DIR,
                        '%s%s' % (uuid.uuid4(), ext))
    hash = hashlib.sha1()
    with open(path, 'wb') as fp:
        for chunk in file.chunks():
            hash.update(chunk)
            fp.write(chunk)
    sha1 = hash.hexdigest()
    email = sig_request['iss']
    log.info('uploaded %r for %s' % (fp.name, email))
    sha1_from_client = str(request.POST['sha1'])
    if sha1_from_client != sha1:
        return http.HttpResponseBadRequest('sha1 hash did not match')
    tasks.process_file.delay(email, fp.name)
    return http.HttpResponse('cool')


@log_exception
@require_upload_key
@json_view
def checkfiles(request, raw_sig_request, sig_request):
    try:
        sha1s = sig_request['request']['sha1s']
    except KeyError:
        return http.HttpResponseBadRequest('malformed request')
    existing = set(TrackFile.objects.filter(sha1__in=sha1s)
                            .values_list('sha1', flat=True))
    check = {}
    for sh in sha1s:
        check[sh] = bool(sh in existing)
    return {'sha1s': check}
