import os
import shutil

from django.conf import settings

from rockit.base.util import filetype
from rockit.music.models import Track, TrackFile, VerifiedEmail


def create_audio_file(source=None, make_mp3=False,
                      make_ogg=False, session=None, **af_params):
    if not source:
        source = os.path.join(os.path.dirname(__file__),
                              'resources', 'sample.mp3')
    if not os.path.exists(settings.UPLOAD_TEMP_DIR):
        os.makedirs(settings.UPLOAD_TEMP_DIR)
    ftype = filetype(source)
    tmp = os.path.join(settings.UPLOAD_TEMP_DIR,
                       '__test__.%s' % ftype)
    if os.path.exists(tmp):
        os.unlink(tmp)
    shutil.copyfile(source, tmp)
    try:
        em = VerifiedEmail.objects.get(email='edna@wat.com')
    except VerifiedEmail.DoesNotExist:
        em = VerifiedEmail.objects.create(email='edna@wat.com')
    params = dict(temp_path=tmp,
                  email=em,
                  artist='Gescom',
                  album='Minidisc',
                  track='Horse')
    params.update(af_params)
    tr = Track.objects.create(**params)

    # These are convenience functions to copy the source into stub locations.
    # Don't rely on them too much.
    if make_mp3:
        TrackFile.objects.create(track=tr,
                                 type='mp3',
                                 sha1='noop',
                                 byte_size=1,
                                 session=session,
                                 s3_url='s3:file.mp3')
    if make_ogg:
        TrackFile.objects.create(track=tr,
                                 type='ogg',
                                 sha1='noop',
                                 byte_size=1,
                                 session=session,
                                 s3_url='s3:file.ogg')
    return tr
