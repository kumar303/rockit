import os
import subprocess
import tempfile

from django.conf import settings

import commonware.log
from celeryutils import task
import pylast

from rockit.music.audio_file import scan_fast
from rockit.music.models import Track, TrackFile, VerifiedEmail
from . import s3

log = commonware.log.getLogger('rockit')


@task
def process_file(user_email, filename, sha1, **kw):
    af = scan_fast(filename)
    artist = af.tpe1()
    album = af.talb()
    track = af.tit2()
    track_num = str(af.mutagen_id3.get('TRCK'))
    track_num = track_num.split('/')[0]  # 1/30
    track_num = int(track_num) if track_num else None
    email, c = VerifiedEmail.objects.get_or_create(email=user_email)
    tr = Track.objects.create(email=email,
                              temp_path=filename,
                              artist=artist,
                              album=album,
                              track=track,
                              track_num=track_num)
    store_mp3.delay(tr.pk, filename, sha1=sha1)
    album_art.delay(tr.pk)


@task
def store_mp3(track_id, filename, sha1=None, **kw):
    print 'starting to store mp3 for %s' % track_id
    tr = Track.objects.get(pk=track_id)
    s3.move_local_file_into_s3_dir(tr.temp_path,
                                   tr.s3_url('mp3'),
                                   make_public=False,
                                   make_protected=True,
                                   unlink_source=False)
    TrackFile.from_file(tr, filename, sha1=sha1)
    print 'mp3 stored for %s' % track_id
    store_ogg.delay(track_id)


@task
def store_ogg(track_id, **kw):
    print 'starting to transcode and store ogg for %s' % track_id
    tr = Track.objects.get(pk=track_id)
    cwd = os.getcwd()
    os.chdir(os.path.dirname(tr.temp_path))
    try:
        frommp3 = subprocess.Popen(['mpg123', '-w', '-',
                                    os.path.basename(tr.temp_path)],
                                   stdout=subprocess.PIPE)
        toogg = subprocess.Popen(['oggenc', '-'],
                                 stdin=frommp3.stdout,
                                 stdout=subprocess.PIPE)
        base, ext = os.path.splitext(os.path.basename(tr.temp_path))
        with tempfile.NamedTemporaryFile('wb', delete=False,
                                         suffix='.ogg') as outfile:
            dest = outfile.name
            print 'transcoding %s -> %s' % (frommp3, dest)
            while True:
                data = toogg.stdout.read(1024 * 100)
                if not data:
                    break
                outfile.write(data)
        ret = toogg.wait()
        if ret != 0:
            raise RuntimeError('oggenc failed')
    finally:
        os.chdir(cwd)
    #p = subprocess.Popen(['ffmpeg', '-i',
    #                      tr.temp_path,
    #                     '-vn', '-acodec', 'vorbis', '-aq', 60, '-strict',
    #                     'experimental', dest])

    s3.move_local_file_into_s3_dir(dest,
                                   tr.s3_url('ogg'),
                                   make_public=False,
                                   make_protected=True,
                                   unlink_source=False,
                                   headers={'Content-Type':
                                                'application/ogg'})
    tf = TrackFile.from_file(tr, dest)
    # The temp ogg file is no longer needed.
    os.unlink(dest)
    # The local mp3 source is no longer needed.
    os.unlink(tr.temp_path)
    print 'stored %s for %s' % (tf.s3_url, track_id)


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
