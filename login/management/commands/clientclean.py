from django.contrib.auth import get_user_model

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from django.db import DEFAULT_DB_ALIAS

from login.models import Client, ClientStatus


class Command(BaseCommand):
    help = 'Clean stale clients'

    def handle(self, *args, **options):

        if options['verbosity'] >= 1:
            self.stdout.write('Cleaning stale clients')

        # Delete online client
        queryset = Client.objects.filter(status=ClientStatus.O.name) | Client.objects.filter(status=ClientStatus.R.name)
        if queryset:
            if options['verbosity'] >= 1:
                self.stdout.write('Disconnecting {} clients'.format(len(queryset)))
            queryset.update(status=ClientStatus.D.name)
        elif options['verbosity'] >= 1:
            self.stdout.write('Found no online clients')

        if options['verbosity'] >= 1:
            self.stdout.write(
                self.style.SUCCESS("Done."))
