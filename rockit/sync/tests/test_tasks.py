from cStringIO import StringIO
import os

from django.conf import settings

import fudge
from fudge.inspector import arg
from nose.tools import eq_

from rockit.music.models import Track
from rockit.sync import tasks
from rockit.sync.tests import create_audio_file
from .base import MP3TestCase


class TestTasks(MP3TestCase):

    def setUp(self):
        super(TestTasks, self).setUp()
        self.sample_m4a = os.path.join(os.path.dirname(__file__),
                                       'resources', 'sample.m4a')
        if not os.path.exists(settings.UPLOAD_TEMP_DIR):
            os.makedirs(settings.UPLOAD_TEMP_DIR)

    def audio_file(self, sample_file=None):
        if not sample_file:
            sample_file = self.sample_path
        return create_audio_file(source=sample_file)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    def test_process_mp3(self, store, album_art):
        store.expects_call()
        album_art.expects('delay')
        tasks.process_file('edna@wat.com', self.sample_path)
        tr = Track.objects.get()
        eq_(tr.email.email, 'edna@wat.com')
        eq_(tr.artist, 'Gescom')
        eq_(tr.album, 'Minidisc')
        eq_(tr.track, 'Horse')
        eq_(tr.track_num, 53)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    def test_process_m4a(self, store, album_art):
        store.expects_call()
        album_art.expects('delay')
        tasks.process_file('edna@wat.com', self.sample_m4a)
        tr = Track.objects.get()
        eq_(tr.email.email, 'edna@wat.com')
        eq_(tr.artist, 'Gescom')
        eq_(tr.album, 'Minidisc')
        eq_(tr.track, 'Horse')
        eq_(tr.track_num, 53)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    @fudge.patch('rockit.sync.tasks.subprocess.Popen')
    def test_track_num_with_total(self, store, album_art, popen):
        store.is_a_stub()
        album_art.is_a_stub()
        data = StringIO(
            '''{"format": {"tags": {"artist": "",
                                    "album": "",
                                    "title": "",
                                    "track": "5/16"}}}''')
        (popen.expects_call().returns_fake()
                             .provides('wait').returns(0)
                             .has_attr(stdout=data))
        tasks.process_file('edna@wat.com', self.sample_path)
        tr = Track.objects.get()
        eq_(tr.track_num, 5)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    @fudge.patch('rockit.sync.tasks.subprocess.Popen')
    def test_empty_track_num(self, store, album_art, popen):
        store.is_a_stub()
        album_art.is_a_stub()
        data = StringIO(
            '''{"format": {"tags": {"artist": "",
                                    "album": "",
                                    "title": "",
                                    "track": ""}}}''')
        (popen.expects_call().returns_fake()
                             .provides('wait').returns(0)
                             .has_attr(stdout=data))
        tasks.process_file('edna@wat.com', self.sample_path)
        tr = Track.objects.get()
        eq_(tr.track_num, None)

    @fudge.patch('rockit.sync.tasks.TaskTree')
    def test_store_and_transcode_mp3(self, Tree):
        (Tree.expects_call().returns_fake()
             .expects('push')
             .with_matching_args(tasks.store_mp3, kwargs=dict(source=True))
             .next_call()
             .with_matching_args(tasks.store_ogg)
             .next_call()
             .with_matching_args(tasks.unlink_source)
             .expects('apply_async')
             )
        tr = self.audio_file()
        tasks.store_and_transcode(tr.pk)

    @fudge.patch('rockit.sync.tasks.TaskTree')
    def test_store_and_transcode_m4a(self, Tree):
        (Tree.expects_call().returns_fake()
             .expects('push')
             .with_matching_args(tasks.store_m4a, kwargs=dict(source=True))
             .next_call()
             .with_matching_args(tasks.store_ogg)
             .next_call()
             .with_matching_args(tasks.unlink_source)
             .expects('apply_async')
             )
        tr = self.audio_file(sample_file=self.sample_m4a)
        tasks.store_and_transcode(tr.pk)

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_mp3(self, s3):
        tr = self.audio_file()
        s3_path = '%s/%s.mp3' % (tr.email.pk, tr.pk)
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(tr.temp_path,
                      s3_path,
                      make_public=False,
                      make_protected=True,
                      unlink_source=False))

        tasks.store_mp3(tr.pk, source=True)

        tr = Track.objects.get(pk=tr.pk)
        tf = tr.file('mp3')
        eq_(tf.s3_url, s3_path)
        eq_(tf.byte_size, 109823)
        eq_(tf.sha1, self.sample_sha1)
        tr = Track.objects.get(pk=tr.pk)
        eq_(tr.source_track_file.pk, tf.pk)

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_m4a(self, s3):
        tr = self.audio_file(sample_file=self.sample_m4a)
        s3_path = '%s/%s.m4a' % (tr.email.pk, tr.pk)
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(tr.temp_path,
                      s3_path,
                      make_public=False,
                      make_protected=True,
                      unlink_source=False))

        tasks.store_m4a(tr.pk, source=True)

        tr = Track.objects.get(pk=tr.pk)
        tf = tr.file('m4a')
        eq_(tf.s3_url, s3_path)
        assert tf.byte_size
        assert tf.sha1
        tr = Track.objects.get(pk=tr.pk)
        eq_(tr.source_track_file.pk, tf.pk)

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_ogg_from_mp3(self, s3):
        tr = self.audio_file()
        s3_path = '%s/%s.ogg' % (tr.email.pk, tr.pk)
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(arg.any(),
                      s3_path,
                      make_public=False,
                      make_protected=True,
                      unlink_source=False,
                      headers={'Content-Type': 'application/ogg'}))

        tasks.store_ogg(tr.pk)

        tr = Track.objects.get(pk=tr.pk)
        tf = tr.file('ogg')
        eq_(tf.s3_url, s3_path)
        eq_(tf.type, 'ogg')
        assert tf.byte_size, 'expected byte size'
        assert tf.sha1, 'expected sha1 hash'

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_ogg_from_m4a(self, s3):
        tr = self.audio_file(sample_file=self.sample_m4a)
        s3_path = '%s/%s.ogg' % (tr.email.pk, tr.pk)
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(arg.any(),
                      s3_path,
                      make_public=False,
                      make_protected=True,
                      unlink_source=False,
                      headers={'Content-Type': 'application/ogg'}))

        tasks.store_ogg(tr.pk)

        tr = Track.objects.get(pk=tr.pk)
        tf = tr.file('ogg')
        eq_(tf.s3_url, s3_path)
        eq_(tf.type, 'ogg')
        assert tf.byte_size, 'expected byte size'
        assert tf.sha1, 'expected sha1 hash'

    @fudge.patch('rockit.sync.tasks.pylast')
    def test_album_art(self, fm):
        (fm.is_a_stub()
           .expects('get_lastfm_network')
           .returns_fake()
           .expects('get_album')
           .returns_fake()
           .expects('get_cover_image')
           .returns('<large URL>')
           .next_call().returns('<medium URL>')
           .next_call().returns('<small URL>'))
        tr = self.audio_file()

        tasks.album_art(tr.pk)

        tr = Track.objects.get(pk=tr.pk)
        eq_(tr.large_art_url, '<large URL>')
        eq_(tr.medium_art_url, '<medium URL>')
        eq_(tr.small_art_url, '<small URL>')
