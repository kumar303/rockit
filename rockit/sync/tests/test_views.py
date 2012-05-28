import json

from django.conf import settings

import fudge
from fudge.inspector import arg
from funfactory.urlresolvers import reverse
import jwt
from nose.tools import eq_

from rockit.music.models import VerifiedEmail, TrackFile
from .base import MP3TestCase


class TestCheckFiles(MP3TestCase):

    def setUp(self):
        super(TestCheckFiles, self).setUp()
        self.email = VerifiedEmail.objects.create(email='edna@wat.com',
                                                  upload_key='sekrets')

    def checkfiles(self, sha1s):
        sig = jwt.encode({'iss': self.email.email, 'aud': settings.SITE_URL,
                          'request': {'sha1s': sha1s}},
                         self.email.upload_key)
        return self.client.get(reverse('sync.checkfiles'),
                               data=dict(r=sig))

    def test_check_false(self):
        resp = self.checkfiles([self.sample_sha1])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], False)

    def test_check_true(self):
        self.create_audio_file()
        resp = self.checkfiles([self.sample_sha1])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], True)

    def test_check_inactive(self):
        self.create_audio_file()
        TrackFile.objects.all().update(is_active=False)
        resp = self.checkfiles([self.sample_sha1])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], False)

    def test_check_multiple(self):
        self.create_audio_file()
        resp = self.checkfiles([self.sample_sha1,
                                'nonexistant'])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], True)
        eq_(data['sha1s']['nonexistant'], False)


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
                                    {'r': sig_request,
                                     'sample.mp3': fp,
                                     'sha1': sha1})

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload(self, process_file):
        process_file.expects('delay').with_args('edna@wat.com', arg.any())
        resp = self.post(sig_request=self.jwt())
        eq_(resp.status_code, 200)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload_existing(self, process_file):
        process_file.provides('delay')
        self.create_audio_file()  # existing file
        resp = self.post(sig_request=self.jwt())
        eq_(resp.status_code, 400)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload_existing_but_inactive(self, process_file):
        process_file.provides('delay')
        self.create_audio_file()  # existing file
        TrackFile.objects.all().update(is_active=False)
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
