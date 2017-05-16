# mqttclient application command

from django.core.management.base import BaseCommand

from ambulances.management.commands._client import Client

class Command(BaseCommand):
    help = 'Connect to the mqtt broker'

    def handle(self, *args, **options):

        client = Client('brian', 'cruzroja',
                        self.stdout, self.style)
                
        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
