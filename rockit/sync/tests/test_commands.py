from nose.tools import eq_
import test_utils

from rockit.music.models import VerifiedEmail
from rockit.sync.management.commands.uploadkey import Command


class TestCommand(test_utils.TestCase):

    def test_upload_key(self):
        Command().handle(email='edna@wat.com', regenerate=False)
        em = VerifiedEmail.objects.get(email='edna@wat.com')
        assert em.upload_key

    def test_no_regeneration(self):
        VerifiedEmail.objects.create(email='edna@wat.com',
                                     upload_key='idonteven')
        Command().handle(email='edna@wat.com', regenerate=False)
        em = VerifiedEmail.objects.get(email='edna@wat.com')
        eq_(em.upload_key, 'idonteven')

    def test_regenerate(self):
        VerifiedEmail.objects.create(email='edna@wat.com',
                                     upload_key='idonteven')
        Command().handle(email='edna@wat.com', regenerate=True)
        em = VerifiedEmail.objects.get(email='edna@wat.com')
        assert em.upload_key != 'idonteven'
