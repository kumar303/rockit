import hashlib
import os

from django.conf import settings
from django.db import models

from rockit.base.models import ModelBase
from rockit.base.util import filetype
from rockit.sync import s3


class VerifiedEmail(ModelBase):
    email = models.CharField(max_length=255, db_index=True, unique=True)
    upload_key = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'music_email'


class Track(ModelBase):
    email = models.ForeignKey(VerifiedEmail)
    is_active = models.BooleanField(default=True, db_index=True)
    temp_path = models.CharField(max_length=255, blank=True, null=True)
    artist = models.CharField(max_length=255, db_index=True)
    album = models.CharField(max_length=255, db_index=True)
    track = models.CharField(max_length=255)
    track_num = models.IntegerField(blank=True, null=True)
    source_track_file = models.ForeignKey('music.TrackFile', null=True,
                                          related_name='+')
    large_art_url = models.CharField(max_length=255, blank=True, null=True)
    medium_art_url = models.CharField(max_length=255, blank=True, null=True)
    small_art_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'music_track'

    def __unicode__(self):
        return u'<%s %s:%s@%s>' % (self.__class__.__name__,
                                   self.artist,
                                   self.track,
                                   self.pk)

    def file(self, type):
        qs = self.files.filter(type=type)
        if qs.count():
            return qs.get()
        else:
            return None

    def to_json(self):
        def _url(path):
            return 'http://%s.s3.amazonaws.com/%s' % (
                                 settings.S3_BUCKET,
                                 path)
        s3_urls = {}
        for tf in self.files.all():
            s3_urls[tf.type] = s3.get_authenticated_url(tf.s3_url)
        return dict(id=self.pk,
                    artist=self.artist,
                    album=self.album,
                    track=self.track,
                    s3_urls=s3_urls,
                    large_art_url=self.large_art_url,
                    medium_art_url=self.medium_art_url,
                    small_art_url=self.small_art_url,
                    # deprecate this:
                    album_art_url=self.large_art_url)

    def s3_url(self, type):
        return '%s/%s.%s' % (self.email.pk, self.pk, type)


class TrackFile(ModelBase):
    track = models.ForeignKey(Track, related_name='files')
    is_active = models.BooleanField(default=True, db_index=True)
    type = models.CharField(max_length=4, db_index=True)
    byte_size = models.IntegerField()
    sha1 = models.CharField(max_length=40, db_index=True)
    s3_url = models.CharField(max_length=255)
    session = models.ForeignKey('sync.SyncSession', null=True)

    class Meta:
        db_table = 'music_track_file'

    @classmethod
    def from_file(cls, track, filename, session_key, source=False):
        """Creates a track file from a filename.

        if source is True it means that this file was the
        original one uploaded for the track.
        """
        hash = hashlib.sha1()
        with open(filename, 'rb') as fp:
            while 1:
                chunk = fp.read(1024 * 100)
                if not chunk:
                    break
                hash.update(chunk)
        sha1 = hash.hexdigest()
        type = filetype(filename)
        tf = cls.objects.create(track=track,
                                sha1=sha1,
                                s3_url=track.s3_url(type),
                                type=type,
                                session_id=session_key,
                                byte_size=os.path.getsize(filename))
        if source:
            Track.objects.filter(pk=track.pk).update(source_track_file=tf)
        return tf
