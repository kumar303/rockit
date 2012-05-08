import json

from django.conf import settings

import fudge
from funfactory.urlresolvers import reverse
import jwt
from nose.tools import eq_
import test_utils

from rockit.sync.tests import create_audio_file


class TestIndex(test_utils.TestCase):

    def setUp(self):
        self.af = create_audio_file(s3_ogg_url='s3:ogg',
                                    s3_mp3_url='s3:mp3')

    def get(self, client_id=None, secret=None):
        if not client_id:
            client_id = settings.API_CLIENTS.keys()[0]
        if not secret:
            secret = settings.API_CLIENTS[client_id]
        req = {'iss': client_id,
               'aud': settings.SITE_URL,
               'request': dict(email='edna@wat.com')}
        return self.client.get(reverse('music.index'),
                               dict(r=jwt.encode(req, secret)))

    @fudge.patch('rockit.music.models.s3')
    def test_success(self, s3):
        s3.expects('get_authenticated_url')
        resp = self.get()
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['songs'][0]['artist'], 'Gescom')
        eq_(data['songs'][0]['album'], 'Minidisc')
        eq_(data['songs'][0]['track'], 'Horse')

    @fudge.patch('rockit.music.models.s3')
    def test_unauthorized(self, s3):
        resp = self.get(secret='invalid')
        eq_(resp.status_code, 403)
