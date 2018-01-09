# mqttclient application command

from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.mqttsubscribe import SubscribeClient

class Command(BaseCommand):
    
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        import os
        
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
        broker['CLIENT_ID'] = broker['CLIENT_ID'] + '_' + str(os.getpid())

        client = SubscribeClient(broker,
                                 self.stdout,
                                 self.style,
                                 verbosity = options['verbosity'])
        
        self.stdout.write(
            self.style.SUCCESS("""* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
* * *                    M Q T T   C L I E N T                    * * *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"""))
        
        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
