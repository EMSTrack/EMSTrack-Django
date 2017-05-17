# mqttclient application command

from django.core.management.base import BaseCommand
from django.conf.settings import settings

from ambulances.management.commands._client import Client

class Command(BaseCommand):
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        broker = {
            'USERNAME': '',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLIENT_ID': 'django',
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        
        client = Client(broker, self.stdout, self.style)
                
        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
