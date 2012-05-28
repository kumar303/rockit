from django.db import models

from rockit.base.models import ModelBase


class SyncSession(ModelBase):
    session_key = models.CharField(max_length=40, primary_key=True)
    is_active = models.BooleanField(default=True, db_index=True)
    email = models.ForeignKey('music.VerifiedEmail')

    class Meta:
        db_table = 'sync_session'
