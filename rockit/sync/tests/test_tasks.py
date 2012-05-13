import os

from django.conf import settings

import fudge
from fudge.inspector import arg
from nose.exc import SkipTest
from nose.tools import eq_

from rockit.music.models import Track
from rockit.sync import tasks
from rockit.sync.tests import create_audio_file
from .base import MP3TestCase


class TestTasks(MP3TestCase):

    def setUp(self):
        super(TestTasks, self).setUp()
        if not os.path.exists(settings.UPLOAD_TEMP_DIR):
            os.makedirs(settings.UPLOAD_TEMP_DIR)

    def audio_file(self):
        return create_audio_file(mp3=self.sample_path)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    def test_process(self, store, album_art):
        store.expects_call()
        album_art.expects('delay')
        tasks.process_file('edna@wat.com', self.sample_path,
                           self.sample_sha1)
        tr = Track.objects.get()
        eq_(tr.email.email, 'edna@wat.com')
        eq_(tr.artist, 'Gescom')
        eq_(tr.album, 'Minidisc')
        eq_(tr.track, 'Horse')
        eq_(tr.track_num, 53)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    @fudge.patch('rockit.sync.tasks.scan_fast')
    def test_track_num_with_total(self, store, album_art, scan_fast):
        store.is_a_stub()
        album_art.is_a_stub()
        id3 = fudge.Fake().provides('get').returns('5/16')
        (scan_fast.expects_call().returns_fake()
                  .is_a_stub()
                  .has_attr(mutagen_id3=id3))
        tasks.process_file('edna@wat.com', self.sample_path,
                           self.sample_sha1)
        tr = Track.objects.get()
        eq_(tr.track_num, 5)

    @fudge.patch('rockit.sync.tasks.store_and_transcode')
    @fudge.patch('rockit.sync.tasks.album_art')
    @fudge.patch('rockit.sync.tasks.scan_fast')
    def test_empty_track_num(self, store, album_art, scan_fast):
        store.is_a_stub()
        album_art.is_a_stub()
        id3 = fudge.Fake().provides('get').returns('')
        (scan_fast.expects_call().returns_fake()
                  .is_a_stub()
                  .has_attr(mutagen_id3=id3))
        tasks.process_file('edna@wat.com', self.sample_path,
                           self.sample_sha1)
        tr = Track.objects.get()
        eq_(tr.track_num, None)

    @fudge.patch('rockit.sync.tasks.store_mp3')
    @fudge.patch('rockit.sync.tasks.store_ogg')
    @fudge.patch('rockit.sync.tasks.unlink_source')
    def test_store_and_transcode(self, store_mp3, store_ogg, unlink_source):
        raise SkipTest("I'm not sure how to test this.")
        tr = self.audio_file()
        for tsk in (store_mp3, store_ogg, unlink_source):
            tsk.expects_call().is_a_stub()
            #(tsk.expects('subtask').with_args(args=[tr.pk], kwargs=arg.any())
            #    .returns('foo'))
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

        tasks.store_mp3(tr.pk)

        tr = Track.objects.get(pk=tr.pk)
        tf = tr.file('mp3')
        eq_(tf.s3_url, s3_path)
        eq_(tf.byte_size, 109823)
        eq_(tf.sha1, self.sample_sha1)

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_ogg(self, s3):
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
