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
    album_art_url = models.CharField(max_length=255, blank=True, null=True)

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
                    album_art_url=self.album_art_url)
