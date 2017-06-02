# mqttseed application command
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from ambulances.management.commands._client import BaseClient

from ambulances.models import Ambulances, Hospital, EquipmentCount, Equipment, Call
from ambulances.serializers import MQTTLocationSerializer, MQTTAmbulanceLocSerializer, MQTTHospitalSerializer, MQTTHospitalEquipmentSerializer, CallSerializer, MQTTHospitalListSerializer
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

        # initialize pubcount
        self.pubcount = 0

        # Seed hospitals
        self.seed_hospital_equipment(client)
        self.seed_hospitals(client)
        self.seed_hospital_config(client)

        # Seed ambulances
        self.seed_ambulance_location(client)
        self.seed_ambulance_status(client)

        # Seed calls
        self.seed_calls(client)

    def publish(self, topic, message, *vargs, **kwargs):
        # increment pubcount then publish
        self.pubcount += 1
        self.client.publish(topic, message, *vargs, **kwargs)

    def seed_ambulance_location(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding ambulance locations"))

        # seeding ambulance locations
        ambulances = Ambulances.objects.all()

        for a in ambulances:
            serializer = MQTTAmbulanceLocSerializer(a)
            json = JSONRenderer().render(serializer.data)

            self.publish('ambulance/{}/location'.format(a.id), json, qos=2, retain=True)
            if self.verbosity > 0:
                self.stdout.write("Location of ambulance {}: {}".format(a.id, serializer.data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding ambulance locations"))

    def seed_ambulance_status(self, client):
        ambulances = Ambulances.objects.all()

        for a in ambulances:
            self.publish('ambulance/{}/status'.format(a.id), a.status.name, qos=2, retain=True)
            if self.verbosity > 0:
                self.stdout.write("Status of ambulance {}: {}".format(a.id, a.status))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding ambulance status"))

    def seed_hospital_equipment(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospitals"))

        # seeding hospitals
        hospitals = Hospital.objects.all()
        k = 0
        for h in hospitals:
            k = k + 1
            if self.verbosity > 0:
                self.stdout.write("  {:2d}. {}".format(k, h))
            equipment = EquipmentCount.objects.filter(hospital=h)
            for e in equipment:
                if self.verbosity > 0:
                    self.stdout.write("      {}: {}".format(e.equipment,
                                                            e.quantity))

                # publish message
                self.publish('hospital/{}/equipment/{}'.format(h.id,
                                                                 e.equipment),
                               e.quantity,
                               qos=2,
                               retain=True)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding hospital equipment"))

    def seed_hospital_config(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital configurations"))

        hospitals = Hospital.objects.all()
        for h in hospitals:
            serializer = MQTTHospitalEquipmentSerializer(h)
            json = JSONRenderer().render(serializer.data)

            self.publish('hospital/{}/metadata'.format(h.id), json, qos=2, retain=True)

            if self.verbosity > 0:
                # print out hospital id + config json
                self.stdout.write("Seeded config for hospital {}".format(h.name))

    def seed_hospitals(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding user hospital lists"))

        # For now, each user will have access to all hospitals
        for user in User.objects.all():
            
            serializer = MQTTHospitalListSerializer(user)
            json = JSONRenderer().render(serializer.data)

            # Publish json - be sure to do this in the seeder
            self.publish('user/{}/hospital'.format(user.username), json, qos=2, retain=True)

            if self.verbosity > 0:
                self.stdout.write(">> Hospital seed - user: {}".format(user.username))

        if self.verbosity > 0:
                self.stdout.write(self.style.SUCCESS(">> Seeded hospital list for every user"))

    def seed_calls(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding calls"))

        for call in Call.objects.all():
            amb_id = call.ambulance.id
            serializer = CallSerializer(call)
            json = JSONRenderer().render(serializer.data)

            self.publish('ambulance/{}/call'.format(amb_id), json, qos=2, retain=True)

            if self.verbosity > 0:
                self.stdout.write(">> Call seed - ambulance: {}".format(amb_id))

        if self.verbosity > 0:
                self.stdout.write(self.style.SUCCESS(">> Seeded calls for every ambulance"))

    # Message publish callback
    def on_publish(self, client, userdata, mid):
        # make sure all is published before disconnecting
        self.pubcount -= 1
        if self.pubcount == 0:
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

        client = Client(broker, self.stdout, self.style,
                        verbosity = options['verbosity'])

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
