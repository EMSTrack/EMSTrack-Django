import base64

from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.contrib.auth.models import User


class Command(BaseCommand):

    help = 'Create mqtt pwfile'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--encode_salt",
            action="store_true",
            default=False,
            help="Encode salt",
        )

    def handle(self, *args, **options):

        if options['verbosity'] >= 1:
            self.stdout.write('Creating mosquitto-auth-plugin compatible pwfile')
            self.stdout.write('encode_salt = {}'.format(options['encode_salt']))

        with open('pwfile', 'w') as file:
            
            # Retrieve current users
            for u in User.objects.filter(is_superuser=True):
                # format django hashed password to match mosquito go auth plugin
                passwd = u.password.replace('pbkdf2_', 'PBKDF2$', 1)
                if options['encode_salt']:
                    # encode salt?
                    parts = passwd.split('$')
                    parts[3] = base64\
                        .b64encode(parts[3].encode('ascii'))\
                        .decode('ascii')
                    passwd = '$'.join(parts)
                # write to file
                file.write('{}:{}\n'.format(u.username, passwd))
        
        if options['verbosity'] >= 1:
            self.stdout.write(
                self.style.SUCCESS("Done."))
