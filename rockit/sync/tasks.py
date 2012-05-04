import os
import subprocess
import tempfile

from django.conf import settings

from celeryutils import task
import pylast

from rockit.music.audio_file import scan_fast
from rockit.music.models import AudioFile
from . import s3

_s3_time_limit = 800


@task
def process_file(user_email, filename, **kw):
    af = scan_fast(filename)
    artist = af.tpe1()
    album = af.talb()
    track = af.tit2()
    au = AudioFile.objects.create(email=user_email,
                                  temp_path=filename,
                                  artist=artist,
                                  album=album,
                                  track=track)
    store_mp3.delay(au.pk)
    album_art.delay(au.pk)


@task(time_limit=_s3_time_limit)
def store_mp3(file_id, **kw):
    print 'starting to store mp3 for %s' % file_id
    au = AudioFile.objects.get(pk=file_id)
    s3_path = '%s/%s.mp3' % (au.email, au.pk)
    s3.move_local_file_into_s3_dir(au.temp_path,
                                   s3_path,
                                   make_public=True,
                                   unlink_source=False)
    au.s3_mp3_url = s3_path
    print 'mp3 stored for %s' % file_id
    store_ogg.delay(file_id)


@task(time_limit=_s3_time_limit)
def store_ogg(file_id, **kw):
    print 'starting to transcode and store ogg for %s' % file_id
    au = AudioFile.objects.get(pk=file_id)
    os.chdir(os.path.dirname(au.temp_path))
    frommp3 = subprocess.Popen(['mpg123', '-w', '-',
                                os.path.basename(au.temp_path)],
                               stdout=subprocess.PIPE)
    toogg = subprocess.Popen(['oggenc', '-'],
                             stdin=frommp3.stdout,
                             stdout=subprocess.PIPE)
    base, ext = os.path.splitext(os.path.basename(au.temp_path))
    with tempfile.NamedTemporaryFile('wb', delete=False) as outfile:
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
    #p = subprocess.Popen(['ffmpeg',
    #                      au.temp_path,
    #                     '-vn', '-acodec', 'vorbis', '-aq', 60, '-strict',
    #                     'experimental',
    #                     ])
    # -i $1 -vn -acodec vorbis -aq 60 -strict experimental $2

    s3_path = '%s/%s.ogg' % (au.email, au.pk)
    s3.move_local_file_into_s3_dir(dest,
                                   s3_path,
                                   make_public=True,
                                   unlink_source=True,
                                   headers={'Content-Type': 'application/ogg'})
    au.s3_ogg_url = s3_path

    au.save()
    print 'stored %s for %s' % (s3_path, file_id)


@task
def album_art(file_id, **kw):
    au = AudioFile.objects.get(pk=file_id)
    try:
        fm = pylast.get_lastfm_network(api_key=settings.LAST_FM_KEY)
        fm_album = fm.get_album(au.artist, au.album)
        #track.lastfm_url_sm_image = \
        #                fm_album.get_cover_image(pylast.COVER_SMALL)
        #track.lastfm_url_med_image = \
        #                fm_album.get_cover_image(pylast.COVER_MEDIUM)
        au.album_art_url = fm_album.get_cover_image(pylast.COVER_LARGE)
    except pylast.WSError:
        # Probably album not found
        raise
    au.save()
    print 'got artwork for %s' % au
