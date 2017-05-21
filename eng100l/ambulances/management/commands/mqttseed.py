# mqttseed application command
from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.management.commands._client import BaseClient

from ambulances.models import Ambulances, Hospital, EquipmentCount, Equipment
from ambulances.serializers import MQTTLocationSerializer, MQTTAmbulanceLocSerializer, MQTTHospitalSerializer
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

class Client(BaseClient):

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        self.seed_hospitals(client)
        self.seed_ambulance_location(client)
        self.seed_hospital_list(client)

        # all done, disconnect
        #self.disconnect()

    def seed_ambulance_location(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding ambulance locations"))

        # seeding ambulance locations
        ambulances = Ambulances.objects.all();

        for a in ambulances:
            serializer = MQTTAmbulanceLocSerializer(a)
            json = JSONRenderer().render(serializer.data)
            
            stream = BytesIO(json)
            data = JSONParser().parse(stream)
            #self.stdout.write(data)
            # Publish json - be sure to do this in the seeder
            client.publish('ambulance/{}/location'.format(a.id), json, qos=2, retain=True)
            if self.verbosity > 0:
                self.stdout.write(" ambulance {} : {}".format(a.id,data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding ambulance locations"))

    def seed_hospitals(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospitals"))

        # seeding hospitals
        hospitals = Hospital.objects.all()
        k = 0
        for h in hospitals:
            k = k + 1
            if self.verbosity > 0:
                self.stdout.write("  {:2d}. {}".format(k, h))
            equipment = EquipmentCount.objects.filter(hospital = h)
            for e in equipment:
                if self.verbosity > 0:
                    self.stdout.write("      {}: {}".format(e.equipment,
                                                            e.quantity))

                # publish message
                client.publish('hospital/{}/equipment/{}'.format(h.id,
                                                                 e.equipment),
                               e.quantity,
                               qos=2,
                               retain=True)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding hospitals"))

    def seed_hospital_list(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding list of hospitals"))

        # seeding list of hospitals with their ids
        hospitals = Hospital.objects.all();

        for h in hospitals:
            serializer = MQTTHospitalSerializer(h)
            json = JSONRenderer().render(serializer.data)

            stream = BytesIO(json)
            data = JSONParser().parse(stream)

            # Publish json - be sure to do this in the seeder
            # TODO change h.id to actual user id.
            client.publish('user/{}/hospital'.format(h.id), json, qos=2, retain=True)

            if self.verbosity > 0:
                self.stdout.write(" hospital {} : {}".format(h.id, data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding list of hosptials"))
            
    # Message publish callback
    def on_publish(self, client, userdata, mid):
        pass

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

        client = Client(broker, self.stdout, self.style,
                        verbosity = options['verbosity'])

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
