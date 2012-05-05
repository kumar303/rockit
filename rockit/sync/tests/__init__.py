import os
import shutil

from django.conf import settings

from rockit.music.models import AudioFile


def create_audio_file(mp3=None, **af_params):
    if not mp3:
        mp3 = os.path.join(os.path.dirname(__file__),
                           'resources', 'sample.mp3')
    if not os.path.exists(settings.UPLOAD_TEMP_DIR):
        os.makedirs(settings.UPLOAD_TEMP_DIR)
    tmp = os.path.join(settings.UPLOAD_TEMP_DIR,
                       '__test__.mp3')
    if os.path.exists(tmp):
        os.unlink(tmp)
    shutil.copyfile(mp3, tmp)
    params = dict(temp_path=tmp,
                  email='edna@wat.com',
                  artist='Gescom',
                  album='Minidisc',
                  track='Horse',
                  byte_size=1)
    params.update(af_params)
    af = AudioFile.objects.create(**params)
    return af
