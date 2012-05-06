import hashlib
import os

import test_utils


class MP3TestCase(test_utils.TestCase):

    def setUp(self):
        self.sample_path = os.path.join(os.path.dirname(__file__),
                                        'resources', 'sample.mp3')
        with self.sample_file() as fp:
            self.sample_sha1 = hashlib.sha1(fp.read()).hexdigest()

    def sample_file(self):
        return open(self.sample_path, 'rb')
