"""
Additional treatment for the loaddata command.
Location example: project/app/management/commands/flush.py
"""

print('> In flush')

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import flush

class Command(flush.Command):

    def handle(self, *args, **options):
        print('> In handle')
        super(Command, self).handle(*args, **options)
