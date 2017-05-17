# mqttseed application command

from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.management.commands._client import BaseClient

from ambulances.models import Hospital, EquipmentCount, Equipment

class Client(BaseClient):

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False
        
        # seeding hospitals
        self.stdout.write(self.style.SUCCESS("Seeding hospitals"))
        hospitals = Hospital.objects.all()
        k = 0
        for h in hospitals:
            k = k + 1
            self.stdout.write(" {:2d}. {}".format(k, h))
            equipment = EquipmentCount.objects.filter(hospital = h)
            for e in equipment:
                self.stdout.write("     {}: {}".format(e.equipment,
                                                           e.quantity))
                # publish message
                client.publish('hospital/{}/equipment/{}'.format(h.id,
                                                                 e.equipment),
                               e.quantity,
                               qos=2,
                               retain=True)
                
        self.stdout.write(self.style.SUCCESS("Done seeding hospitals"))

        # all done, disconnect
        self.disconnect()

class Command(BaseCommand):
    help = 'Seed the mqtt broker'

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
