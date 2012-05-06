import test_utils

from rockit.music.models import VerifiedEmail
from rockit.sync.management.commands.uploadkey import Command


class TestCommand(test_utils.TestCase):

    def test_upload_key(self):
        Command().handle(email='edna@wat.com')
        em = VerifiedEmail.objects.get(email='edna@wat.com')
        assert em.upload_key
