from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.db import DEFAULT_DB_ALIAS

import hashlib, os
from base64 import b64encode, b64decode

class Command(BaseCommand):
    help = 'Create admin user'

    def make_hash(password,
                  salt_length = 12,
                  key_length = 24,
                  hash_function = 'sha256',
                  iterations = 901):

        password = password.encode('utf-8')
        salt = b64encode(os.urandom(salt_length))

        key = hashlib.pbkdf2_hmac(hash_function,
                                  password,
                                  salt,
                                  iterations,
                                  128)
        
        return 'PBKDF2${}${}${}${}'.format(hash_functions,
                                           iterations,
                                           salt,
                                           b64encode(key))
    
    def handle(self, *args, **options):

        if options['verbosity'] >= 1:
            self.stdout.write('> Bootstraping ambulance application')
        
        # Retrieve defaults from settings
        mqtt = {
            'USERNAME': '',
            'PASSWORD': '',
        }
        mqtt.update(settings.MQTT)

        # Retrieve current user model
        model = get_user_model()
        username_field = model._meta.get_field(model.USERNAME_FIELD)

        user_data = {}
        username = username_field.clean(mqtt['USERNAME'], None)
        database = DEFAULT_DB_ALIAS
        
        if not username:
            raise CommandError("Could not retrieve '{}' from settings.".format(model.USERNAME_FIELD))

        # Make sure mandatory fields are present
        for field_name in model.REQUIRED_FIELDS:
            if mqtt[field_name.upper()]:
                field = model._meta.get_field(field_name)
                user_data[field_name] = field.clean(mqtt[field_name.upper()], None)
            else:
                raise CommandError("Could not retrieve '{}' from settings.".format(field_name))

        if username:

            print('hash = {}'.format(make_hash('password')))

            
            # create superuser
            user_data[model.USERNAME_FIELD] = username
            user_data['password'] = mqtt['PASSWORD']
            model._default_manager.db_manager(database).create_superuser(**user_data)

            # generate password file
            
            if options['verbosity'] >= 1:
                self.stdout.write(
                    self.style.SUCCESS("Superuser created successfully."))

