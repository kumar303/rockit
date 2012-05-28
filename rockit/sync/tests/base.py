import hashlib
import os

import test_utils

from rockit.music.models import Track, TrackFile


class MP3TestCase(test_utils.TestCase):

    def setUp(self):
        self.sample_path = os.path.join(os.path.dirname(__file__),
                                        'resources', 'sample.mp3')
        with self.sample_file() as fp:
            self.sample_sha1 = hashlib.sha1(fp.read()).hexdigest()

    def sample_file(self):
        return open(self.sample_path, 'rb')

    def create_audio_file(self):
        tr = Track.objects.create(email=self.email,
                                  artist='Flying Lotus',
                                  track='Arkestry',
                                  album='Cosmogramma')
        TrackFile.objects.create(track=tr,
                                 byte_size=1,
                                 sha1=self.sample_sha1)
