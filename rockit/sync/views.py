import hashlib
import os
import uuid

from django.conf import settings
from django import http
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

import commonware.log
import jwt

from rockit.music.models import AudioFile, VerifiedEmail
from . import tasks
from .decorators import (post_required, log_exception,
                         remote_jsonp_view)

log = commonware.log.getLogger('rockit')


def index(request):
    return http.HttpResponse('sync server!')


@remote_jsonp_view
def songs(request):
    email = get_object_or_404(VerifiedEmail, email=request.GET.get('email'))
    af = (AudioFile.objects.filter(email=email)
                           .exclude(s3_ogg_url=None)
                           .order_by('-created'))
    ob = []
    for afile in af.all():
        ob.append(afile.to_json())
    return {'songs': ob}


@post_required
@csrf_exempt
@log_exception
def upload(request):
    raw_sig_request = str(request.POST.get('sig_request'))
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
    print 'wrote %s' % fp.name
    print key, file
    sha1_from_client = str(request.POST['sha1'])
    if sha1_from_client != sha1:
        return http.HttpResponseBadRequest('sha1 hash did not match')
    tasks.process_file.delay(user_email, fp.name, sha1_from_client)
    return http.HttpResponse('cool')
