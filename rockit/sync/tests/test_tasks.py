import os
import shutil

from django.conf import settings

import fudge
from fudge.inspector import arg
from nose.tools import eq_
import test_utils

from rockit.music.models import AudioFile
from rockit.sync import tasks


class TestTasks(test_utils.TestCase):

    def setUp(self):
        self.mp3 = os.path.join(os.path.dirname(__file__),
                                'resources',
                                'sample.mp3')
        if not os.path.exists(settings.UPLOAD_TEMP_DIR):
            os.makedirs(settings.UPLOAD_TEMP_DIR)

    def audio_file(self):
        tmp = os.path.join(settings.UPLOAD_TEMP_DIR,
                           '__test__.mp3')
        if os.path.exists(tmp):
            os.unlink(tmp)
        shutil.copyfile(self.mp3, tmp)
        af = AudioFile.objects.create(temp_path=tmp,
                                      email='edna@wat.com',
                                      artist='Gescom',
                                      album='Minidisc',
                                      track='Horse',
                                      byte_size=1)
        return af

    @fudge.patch('rockit.sync.tasks.store_mp3')
    @fudge.patch('rockit.sync.tasks.album_art')
    def test_process(self, store_mp3, album_art):
        store_mp3.expects('delay')
        album_art.expects('delay')
        tasks.process_file('edna@wat.com', self.mp3)
        af = AudioFile.objects.get()
        eq_(af.email, 'edna@wat.com')
        eq_(af.artist, 'Gescom')
        eq_(af.album, 'Minidisc')
        eq_(af.track, 'Horse')
        eq_(af.byte_size, 109823)

    @fudge.patch('rockit.sync.tasks.s3')
    @fudge.patch('rockit.sync.tasks.store_ogg')
    def test_store_mp3(self, s3, store_ogg):
        store_ogg.expects('delay')
        af = self.audio_file()
        s3_path = 'edna@wat.com/%s.mp3' % af.pk
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(af.temp_path,
                      s3_path,
                      make_public=True,
                      unlink_source=False))

        tasks.store_mp3(af.pk)

        af = AudioFile.objects.get(pk=af.pk)
        eq_(af.s3_mp3_url, s3_path)

    @fudge.patch('rockit.sync.tasks.s3')
    def test_store_ogg(self, s3):
        af = self.audio_file()
        s3_path = 'edna@wat.com/%s.ogg' % af.pk
        (s3.expects('move_local_file_into_s3_dir')
           .with_args(arg.any(),
                      s3_path,
                      make_public=True,
                      unlink_source=True,
                      headers={'Content-Type': 'application/ogg'}))

        tasks.store_ogg(af.pk)

        af = AudioFile.objects.get(pk=af.pk)
        eq_(af.s3_ogg_url, s3_path)

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
        af = self.audio_file()

        tasks.album_art(af.pk)

        af = AudioFile.objects.get(pk=af.pk)
        eq_(af.large_art_url, '<large URL>')
        eq_(af.medium_art_url, '<medium URL>')
        eq_(af.small_art_url, '<small URL>')
