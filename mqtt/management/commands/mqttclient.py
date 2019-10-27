import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from mqtt.subscribe import SubscribeClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        import os

        broker = {
            'USERNAME': '',
            'PASSWORD': '',
            'HOST': settings.MQTT['BROKER_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLIENT_ID': 'django',
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = broker['CLIENT_ID'] + '_' + str(os.getpid())

        client = SubscribeClient(broker,
                                 stdout=self.stdout,
                                 style=self.style,
                                 verbosity=options['verbosity'])

        logger.info("* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")
        logger.info("* * *                    M Q T T   C L I E N T                    * * *")
        logger.info("* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *")

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
