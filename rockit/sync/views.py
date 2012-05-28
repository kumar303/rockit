import hashlib
import os
import uuid

from django.conf import settings
from django.db import transaction
from django import http
from django.views.decorators.csrf import csrf_exempt

import commonware.log

from rockit.base.util import chunked
from rockit.music.models import TrackFile, Track, VerifiedEmail
from . import tasks
from .decorators import (post_required, log_exception,
                         json_view, require_upload_key)
from .models import SyncSession

log = commonware.log.getLogger('rockit')


def index(request):
    return http.HttpResponse('sync server!')


@post_required
@csrf_exempt
@log_exception
@require_upload_key
@transaction.commit_on_success
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
    user_email = sig_request['iss']
    email, c = VerifiedEmail.objects.get_or_create(email=user_email)

    # Check the session.
    try:
        session = SyncSession.objects.get(email=email, is_active=True)
    except:
        log.exception('joining session for %s in upload' % email.email)
        return http.HttpResponseBadRequest('error joining session')

    # Check for existing files.
    if TrackFile.objects.filter(sha1=sha1,
                                is_active=True).count():
        log.info('client uploaded a file that already exists: %s'
                 % sha1)
        os.unlink(path)
        return http.HttpResponseBadRequest('track already exists')

    log.info('uploaded %r for %s' % (fp.name, email.email))
    sha1_from_client = str(sig_request['request']['sha1'])
    if sha1_from_client != sha1:
        log.info('client computed hash %s did not match server '
                 'computed hash %s' % (sha1_from_client, sha1))
        os.unlink(path)
        return http.HttpResponseBadRequest('sha1 hash did not match')

    tasks.process_file.delay(email.email, fp.name, session.session_key)

    return http.HttpResponse('cool')


@post_required
@csrf_exempt
@log_exception
@require_upload_key
@json_view
@transaction.commit_on_success
def checkfiles(request, raw_sig_request, sig_request):
    try:
        session_key = sig_request['request']['session_key']
        sha1s = sig_request['request']['sha1s']
    except KeyError:
        log.exception('in checkfiles')
        return http.HttpResponseBadRequest('malformed request')
    session = SyncSession.objects.get(pk=session_key)
    all_files = TrackFile.objects.filter(sha1__in=sha1s, is_active=True)
    existing = set()
    log.info('checking files for upload session %s' % session_key)
    print ('checking files for upload session %s' % session_key)
    for sh in all_files:
        existing.add(sh.sha1)

    # touch the files and track to prevent deletion on sync.
    all_files.update(session=session)
    (Track.objects.filter(files__sha1__in=sha1s, is_active=True)
                  .update(session=session))

    check = {}
    for sh in sha1s:
        check[sh] = bool(sh in existing)
    return {'sha1s': check}


@post_required
@csrf_exempt
@log_exception
@require_upload_key
@json_view
@transaction.commit_on_success
def start(request, raw_sig_request, sig_request):
    success = True
    message = ''
    session_key = None
    email = VerifiedEmail.objects.get(email=sig_request['iss'])
    if SyncSession.objects.filter(email=email, is_active=True).count():
        success = False
        message = 'Session already in progress for this user'
    else:
        sk = request.session.session_key
        sess = SyncSession.objects.create(session_key=sk, email=email)
        session_key = sess.session_key
    return {'session_key': session_key, 'success': success,
            'message': message}


@post_required
@csrf_exempt
@log_exception
@require_upload_key
@json_view
@transaction.commit_on_success
def finish(request, raw_sig_request, sig_request):
    success = True
    message = ''
    email = VerifiedEmail.objects.get(email=sig_request['iss'])
    try:
        session_key = sig_request['request']['session_key']
        purge = sig_request['request']['purge']
    except KeyError:
        return http.HttpResponseBadRequest('missing params')
    qs = SyncSession.objects.filter(email=email, is_active=True,
                                    pk=session_key)
    if not qs.count():
        success = False
        message = 'no session in progress to finish'
    else:
        session = qs.get()
        log.info('finishing session %s' % session.pk)
        session.is_active = False
        session.save()
        if purge:
            log.info('purging files after upload %s' % session.pk)
            # Delete all files that were not uploaded or
            # touched by this sync session.
            qs = (Track.objects.filter(session__email=email,
                                       is_active=True)
                               .exclude(session=session)
                               .values_list('id', flat=True))
            for track_ids in chunked(qs, 10):
                tasks.delete_tracks.delay(track_ids)

    return {'success': success, 'message': message}
