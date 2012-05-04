import os

from django.conf import settings
from django.db import models

from rockit.base.models import ModelBase


class AudioFile(ModelBase):
    temp_path = models.CharField(max_length=255)
    email = models.CharField(max_length=255, db_index=True)
    artist = models.CharField(max_length=255, db_index=True)
    album = models.CharField(max_length=255, db_index=True)
    track = models.CharField(max_length=255)
    s3_mp3_url = models.CharField(max_length=255, blank=True, null=True)
    s3_ogg_url = models.CharField(max_length=255, blank=True, null=True)
    large_art_url = models.CharField(max_length=255, blank=True, null=True)
    medium_art_url = models.CharField(max_length=255, blank=True, null=True)
    small_art_url = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return u'<%s %s:%s@%s>' % (self.__class__.__name__,
                                   self.artist,
                                   self.track,
                                   self.pk)

    def to_json(self):
        def _url(path):
            return 'http://%s.s3.amazonaws.com/%s' % (
                                 settings.S3_BUCKET,
                                 path)
        return dict(artist=self.artist,
                    album=self.album,
                    track=self.track,
                    s3_mp3_url=_url(self.s3_mp3_url),
                    s3_ogg_url=_url(self.s3_ogg_url),
                    large_art_url=self.large_art_url,
                    medium_art_url=self.medium_art_url,
                    small_art_url=self.small_art_url,
                    # deprecate this:
                    album_art_url=self.large_art_url)
