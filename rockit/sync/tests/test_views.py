import json

from django.conf import settings

import fudge
from fudge.inspector import arg
from funfactory.urlresolvers import reverse
import jwt
from nose.tools import eq_
import test_utils

from rockit.music.models import VerifiedEmail
from rockit.sync.tests import create_audio_file
from .base import MP3TestCase


class TestSongs(test_utils.TestCase):

    def setUp(self):
        self.af = create_audio_file(s3_ogg_url='s3:ogg',
                                    s3_mp3_url='s3:mp3')

    @fudge.patch('rockit.music.models.s3')
    def test_songs(self, s3):
        s3.expects('get_authenticated_url')
        resp = self.client.get(reverse('sync.songs'),
                               dict(email='edna@wat.com'),
                               follow=True)
        eq_(resp.status_code, 200)
        data = json.loads(resp.content)
        eq_(data['songs'][0]['artist'], 'Gescom')
        eq_(data['songs'][0]['album'], 'Minidisc')
        eq_(data['songs'][0]['track'], 'Horse')


class TestUpload(MP3TestCase):

    def setUp(self):
        super(TestUpload, self).setUp()
        self.key = 'in the library with a candlestick'
        self.email = VerifiedEmail.objects.create(email='edna@wat.com',
                                                  upload_key=self.key)

    def jwt(self, key=None):
        req = {'iss': self.email.email,
               'aud': settings.SITE_URL}
        if not key:
            key = self.key
        return jwt.encode(req, key)

    def post(self, sig_request=None, sha1=None):
        if not sha1:
            sha1 = self.sample_sha1
        with self.sample_file() as fp:
            return self.client.post(reverse('sync.upload'),
                                    {'sig_request': sig_request,
                                     'sample.mp3': fp,
                                     'sha1': sha1})

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload(self, process_file):
        process_file.expects('delay').with_args('edna@wat.com', arg.any(),
                                                self.sample_sha1)
        resp = self.post(sig_request=self.jwt())
        eq_(resp.status_code, 200)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_denied(self, process_file):
        # Upload without authorization:
        resp = self.post(sig_request=self.jwt('bad key'))
        eq_(resp.status_code, 403)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_no_key(self, process_file):
        self.email.upload_key = None
        self.email.save()
        resp = self.post(sig_request=self.jwt('bad key'))
        eq_(resp.status_code, 403)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_garbage(self, process_file):
        resp = self.post(sig_request='<garbage>')
        eq_(resp.status_code, 403)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_bad_hash(self, process_file):
        resp = self.post(sig_request=self.jwt(), sha1='<invalid>')
        eq_(resp.status_code, 400)
