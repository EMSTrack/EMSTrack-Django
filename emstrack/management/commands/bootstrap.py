from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.db import DEFAULT_DB_ALIAS
from django.db import IntegrityError


class Command(BaseCommand):

    help = 'Create admin user'

    def create_user(self, user, type_of_user, **options):

        # Retrieve current user model
        model = get_user_model()
        username_field = model._meta.get_field(model.USERNAME_FIELD)

        user_data = {}
        username = username_field.clean(user['USERNAME'], None)
        database = DEFAULT_DB_ALIAS

        if not username:
            raise CommandError("Could not retrieve '{}' from settings.".format(model.USERNAME_FIELD))

        # Make sure mandatory fields are present
        for field_name in model.REQUIRED_FIELDS:
            if user[field_name.upper()]:
                field = model._meta.get_field(field_name)
                user_data[field_name] = field.clean(user[field_name.upper()], None)
            else:
                raise CommandError("Could not retrieve '{}' from settings.".format(field_name))

        if username:

            # create superuser
            user_data[model.USERNAME_FIELD] = username
            user_data['password'] = user['PASSWORD']
            model._default_manager.db_manager(database).create_superuser(**user_data)

            if options['verbosity'] >= 1:
                self.stdout.write(
                    self.style.SUCCESS("{} created successfully.".format(type_of_user)))

    def handle(self, *args, **options):

        if options['verbosity'] >= 1:
            self.stdout.write('Bootstraping ambulance application')
        
        # Retrieve defaults from settings
        superuser = {
            'USERNAME': '',
            'PASSWORD': '',
        }
        superuser.update(settings.MQTT)

        guestuser = {
            'USERNAME': '',
            'PASSWORD': '',
        }
        guestuser.update(settings.GUEST)

        try:

            # create superuser
            self.create_user(superuser, 'Superuser', **options)

        except IntegrityError as e:
            self.stdout.write(self.style.WARNING("Superuser created successfully."))

        try:

            # create guest user
            self.create_user(guestuser, 'Guest user', **options)

        except IntegrityError as e:
            self.stdout.write(self.style.WARNING("Guest user created successfully."))

        if options['verbosity'] >= 1:
            self.stdout.write(
                self.style.SUCCESS("Done."))
