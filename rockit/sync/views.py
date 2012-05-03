import os
import uuid

from django.conf import settings
from django import http
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import commonware.log

from rockit.music.models import AudioFile
from . import tasks
from .decorators import (post_required, log_exception,
                         remote_jsonp_view)

log = commonware.log.getLogger('playdoh')



def index(request):
    return http.HttpResponse('sync server!')


@remote_jsonp_view
def songs(request):
    email = request.GET.get('email')
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
    user_email = request.POST['email']
    if not os.path.exists(settings.UPLOAD_TEMP_DIR):
        log.info('creating upload temp dir')
        os.makedirs(settings.UPLOAD_TEMP_DIR)
    for key, file in request.FILES.items():
        _, ext = os.path.splitext(key)
        path = os.path.join(settings.UPLOAD_TEMP_DIR,
                            '%s%s' % (uuid.uuid4(), ext))
        with open(path, 'wb') as fp:
            for chunk in file.chunks():
                fp.write(chunk)
        print 'wrote %s' % fp.name
        print key, file
        tasks.process_file.delay(user_email, fp.name)
    return http.HttpResponse('cool')
