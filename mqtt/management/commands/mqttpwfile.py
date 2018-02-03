from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.contrib.auth.models import User

class Command(BaseCommand):

    help = 'Create mqtt pwfile'

    def handle(self, *args, **options):

        if options['verbosity'] >= 1:
            self.stdout.write('Creating mosquitto-auth-plugin compatible pwfile')

        with open('pwfile', 'w') as file:
            
            # Retrieve current users
            for u in User.objects.filter(is_superuser=True):
                file.write('{}:{}\n'.format(u.username,
                                            u.password.replace('pbkdf2_',
                                                               'PBKDF2$',1)))
        
        if options['verbosity'] >= 1:
            self.stdout.write(
                self.style.SUCCESS("Done."))
