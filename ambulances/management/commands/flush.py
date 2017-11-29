"""
Additional treatment for the loaddata command.
Location example: project/app/management/commands/loaddata.py
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata


class Command(loaddata.Command):

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
        self.stdout.write("Here is a further treatment! :)")
