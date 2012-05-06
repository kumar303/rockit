import base64
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from rockit.music.models import VerifiedEmail


def generate_key(byte_length):
    """Return a true random ascii string that is byte_length long.

    The resulting key is suitable for cryptogrpahy.
    """
    if byte_length < 32:  # at least 256 bit
        raise ValueError('um, %s is probably not long enough for cryptography'
                         % byte_length)
    key = os.urandom(byte_length)
    key = base64.b64encode(key).rstrip('=')  # strip off padding
    key = key[0:byte_length]
    return key


class Command(BaseCommand):
    help = 'Generate a siging key for uploads'
    option_list = BaseCommand.option_list + (
        make_option('--email', action='store',
                    help='verified email to grant the key to'),
    )

    def handle(self, *args, **options):
        if not options.get('email'):
            raise CommandError('--email is required')
        email, c = VerifiedEmail.objects.get_or_create(email=options['email'])
        key = generate_key(64)
        email.upload_key = key
        email.save()
        print 'email: %s' % options['email']
        print 'key: %s' % key
