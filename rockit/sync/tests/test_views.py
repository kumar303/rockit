import json

from django.conf import settings

import fudge
from fudge.inspector import arg
from funfactory.urlresolvers import reverse
import jwt
from nose.tools import eq_

from rockit.music.models import VerifiedEmail, TrackFile
from rockit.sync.models import SyncSession
from .base import MP3TestCase


class TestCheckFiles(MP3TestCase):

    def setUp(self):
        super(TestCheckFiles, self).setUp()
        self.email = VerifiedEmail.objects.create(email='edna@wat.com',
                                                  upload_key='sekrets')
        self.session = SyncSession.objects.create(session_key='1234',
                                                  email=self.email)
        self.session_key = self.session.session_key

    def checkfiles(self, sha1s):
        sig = jwt.encode({'iss': self.email.email, 'aud': settings.SITE_URL,
                          'request': {'sha1s': sha1s,
                                      'session_key': self.session_key}},
                         self.email.upload_key)
        res = self.client.post(reverse('sync.checkfiles'),
                               data=dict(r=sig))
        eq_(res.status_code, 200)
        return res

    def test_check_false(self):
        resp = self.checkfiles([self.sample_sha1])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], False)

    def test_check_true(self):
        self.create_audio_file()
        resp = self.checkfiles([self.sample_sha1])
        data = json.loads(resp.content)
        eq_(data['sha1s'][self.sample_sha1], True)
        qs = (TrackFile.objects.all().distinct('session__session_key')
                       .values_list('session__session_key', flat=True))
        eq_(list(qs), [self.session_key])

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


class UploadTest(MP3TestCase):

    def setUp(self):
        super(UploadTest, self).setUp()
        self.key = 'in the library with a candlestick'
        self.email = VerifiedEmail.objects.create(email='edna@wat.com',
                                                  upload_key=self.key)

    def jwt(self, key=None, request=None):
        req = {'iss': self.email.email,
               'aud': settings.SITE_URL}
        if request:
            req['request'] = request
        if not key:
            key = self.key
        return jwt.encode(req, key)


class TestUpload(UploadTest):

    def setUp(self):
        super(TestUpload, self).setUp()
        self.session = SyncSession.objects.create(session_key='1234',
                                                  email=self.email)
        self.session_key = self.session.session_key

    def post(self, sig_request=None, request=None):
        if not sig_request:
            if not request:
                request = {}
            request.setdefault('sha1', self.sample_sha1)
            request.setdefault('session_key', self.session_key)
            sig_request = self.jwt(request=request)
        with self.sample_file() as fp:
            return self.client.post(reverse('sync.upload'),
                                    {'r': sig_request,
                                     'sample.mp3': fp})

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload(self, process_file):
        process_file.expects('delay').with_args('edna@wat.com', arg.any(),
                                                self.session_key)
        resp = self.post()
        eq_(resp.status_code, 200)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload_existing(self, process_file):
        process_file.provides('delay')
        self.create_audio_file()  # existing file
        resp = self.post()
        eq_(resp.status_code, 400)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_upload_existing_but_inactive(self, process_file):
        process_file.provides('delay')
        self.create_audio_file()  # existing file
        TrackFile.objects.all().update(is_active=False)
        resp = self.post()
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
        resp = self.post(request=dict(sha1='<invalid>'))
        eq_(resp.status_code, 400)

    @fudge.patch('rockit.sync.tasks.process_file')
    def test_inactive_session(self, process_file):
        self.session.is_active = False
        self.session.save()
        resp = self.post()
        eq_(resp.status_code, 400)


class TestSession(UploadTest):

    def setUp(self):
        super(TestSession, self).setUp()

    def post(self, sig_request=None, expected_status=200):
        if not sig_request:
            sig_request = self.jwt()
        res = self.client.post(reverse('sync.start'),
                               {'r': sig_request})
        eq_(res.status_code, expected_status)
        res = json.loads(res.content)
        return res

    def test_start(self):
        data = self.post()
        us = SyncSession.objects.get(pk=data['session_key'])
        eq_(us.is_active, True)
        eq_(us.email.email, 'edna@wat.com')
        eq_(data['success'], True)

    def test_collision(self):
        data = self.post()
        data = self.post()  # colliding session
        eq_(data['success'], False)
