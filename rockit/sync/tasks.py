import json
import os
import subprocess
import tempfile

from django.conf import settings

import commonware.log
from celery_tasktree import task_with_callbacks, TaskTree
from celeryutils import task
import pylast

from rockit.base.util import filetype
from rockit.music.models import Track, TrackFile, VerifiedEmail
from . import s3

log = commonware.log.getLogger('rockit')


@task
def process_file(user_email, filename, **kw):
    sp = subprocess.Popen(['ffprobe', '-v', 'quiet', '-print_format',
                           'json', '-show_format', '-show_streams',
                           filename],
                          stdout=subprocess.PIPE)
    data = json.load(sp.stdout)
    ret = sp.wait()
    if ret != 0:
        raise RuntimeError('ffprobe failed')
    artist = data['format']['tags']['artist']
    album = data['format']['tags']['album']
    track = data['format']['tags']['title']
    track_num = data['format']['tags']['track']
    track_num = track_num.split('/')[0]  # 1/30
    track_num = int(track_num) if track_num else None
    email, c = VerifiedEmail.objects.get_or_create(email=user_email)
    tr = Track.objects.create(email=email,
                              temp_path=filename,
                              artist=artist,
                              album=album,
                              track=track,
                              track_num=track_num)
    album_art.delay(tr.pk)
    store_and_transcode(tr.pk)


def store_and_transcode(track_id):
    tr = Track.objects.get(pk=track_id)
    ftype = filetype(tr.temp_path)
    transcoders = [store_ogg]
    if ftype == 'mp3':
        store_source = store_mp3
    elif ftype == 'm4a':
        store_source = store_m4a
    else:
        raise ValueError('file type not supported: %r' % ftype)

    args = [tr.pk]
    pipeline = TaskTree()
    pipeline.push(store_source, args=args, kwargs=dict(source=True))
    for trans in transcoders:
        pipeline.push(trans, args=args)
    pipeline.push(unlink_source, args=args)
    pipeline.apply_async()


@task_with_callbacks
def store_mp3(track_id, source=False, **kw):
    _store_source(track_id, 'mp3', source=source)


@task_with_callbacks
def store_m4a(track_id, source=False, **kw):
    _store_source(track_id, 'm4a', source=source)


@task_with_callbacks
def store_ogg(track_id, source=False, **kw):
    print 'starting to transcode and store ogg for %s' % track_id
    tr = Track.objects.get(pk=track_id)
    with tempfile.NamedTemporaryFile('wb', delete=False,
                                     suffix='.ogg') as outfile:
        dest = outfile.name
    sp = subprocess.Popen(['ffmpeg', '-i',
                           tr.temp_path,
                           '-vn', '-acodec', 'vorbis', '-aq', '60', '-strict',
                           'experimental', '-loglevel', 'quiet', '-y', dest])
    ret = sp.wait()
    if ret != 0:
        raise RuntimeError('ffmpeg source->ogg failed')

    s3.move_local_file_into_s3_dir(dest,
                                   tr.s3_url('ogg'),
                                   make_public=False,
                                   make_protected=True,
                                   unlink_source=False,
                                   headers={'Content-Type':
                                                'application/ogg'})
    tf = TrackFile.from_file(tr, dest, source=source)
    # The temp ogg file is no longer needed.
    os.unlink(dest)
    print 'stored %s for %s' % (tf.s3_url, track_id)


@task_with_callbacks
def unlink_source(track_id, **kw):
    tr = Track.objects.get(pk=track_id)
    print 'unlnking temp source %r for %s' % (tr.temp_path, tr.pk)
    os.unlink(tr.temp_path)
    Track.objects.filter(pk=tr.pk).update(temp_path=None)


@task
def album_art(track_id, **kw):
    tr = Track.objects.get(pk=track_id)
    try:
        fm = pylast.get_lastfm_network(api_key=settings.LAST_FM_KEY)
        alb = fm.get_album(tr.artist, tr.album)
        (Track.objects.filter(pk=track_id)
         .update(large_art_url=alb.get_cover_image(pylast.COVER_LARGE),
                 medium_art_url=alb.get_cover_image(pylast.COVER_MEDIUM),
                 small_art_url=alb.get_cover_image(pylast.COVER_SMALL)))
    except pylast.WSError:
        # Probably album not found
        raise
    print 'got artwork for %s' % tr


def _store_source(track_id, ftype, source=False):
    tr = Track.objects.get(pk=track_id)
    print 'starting to store %s for %s from %s' % (ftype, track_id,
                                                   tr.temp_path)
    if filetype(tr.temp_path) != ftype:
        raise ValueError('%s is not of type %s' % (tr.temp_path, ftype))
    s3.move_local_file_into_s3_dir(tr.temp_path,
                                   tr.s3_url(ftype),
                                   make_public=False,
                                   make_protected=True,
                                   unlink_source=False)
    TrackFile.from_file(tr, tr.temp_path, source=source)
    print '%s stored for %s' % (ftype, track_id)
