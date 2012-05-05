import json

from funfactory.urlresolvers import reverse
from nose.tools import eq_
import test_utils

from rockit.sync.tests import create_audio_file


class TestSongs(test_utils.TestCase):

    def setUp(self):
        self.af = create_audio_file(s3_ogg_url='s3:ogg',
                                    s3_mp3_url='s3:mp3')

    def test_songs(self):
        resp = self.client.get(reverse('sync.songs'),
                               dict(email='edna@wat.com'),
                               follow=True)
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['songs'][0]['artist'], 'Gescom')
        eq_(data['songs'][0]['album'], 'Minidisc')
        eq_(data['songs'][0]['track'], 'Horse')
