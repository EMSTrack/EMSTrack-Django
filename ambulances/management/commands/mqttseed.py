# mqttseed application command
from django.core.management.base import BaseCommand
from django.conf import settings

from ambulances.mqttupdate import UpdateClient

from ambulances.models import Ambulance, Hospital, EquipmentCount, Equipment, Call, User
from ambulances.serializers import MQTTLocationSerializer, MQTTAmbulanceLocSerializer, MQTTHospitalSerializer, MQTTHospitalEquipmentSerializer, CallSerializer, MQTTHospitalListSerializer, MQTTAmbulanceListSerializer

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
        self.can_disconnect = False

        # Seed hospitals
        self.seed_hospital_data(client)
        self.seed_hospital_equipment_data(client)
        self.seed_hospital_metadata(client)

        # Seed ambulances
        self.seed_ambulance_data(client)

        # Seed calls
        # self.seed_calls(client)

        # Good to disconnect
        self.can_disconnect = True
        
    def publish(self, topic, message, *vargs, **kwargs):

        # increment pubcount then publish
        self.pubcount += 1
        self.client.publish(topic, message, *vargs, **kwargs)

    def seed_ambulance_data(self, client):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding ambulance data"))

        # seeding ambulances
        ambulances = Ambulance.objects.all()

        for obj in ambulances:
            serializer = AmbulanceSerializer(obj)
            client.update_topic('ambulance/{}/data'.format(obj.id),
                                serializer,
                                qos=2,
                                retain=True)
            
            if self.verbosity > 0:
                self.stdout.write("   Ambulance {}: {}".format(obj.id,
                                                               serializer.data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding ambulance data"))

    def seed_hospital_data(self, client):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital data"))

        # seeding hospital 
        hospitals = Hospital.objects.all()

        for obj in hospitals:
            serializer = HospitalSerializer(obj)
            client.update_topic('hospital/{}/data'.format(obj.id),
                                serializer,
                                qos=2,
                                retain=True)
            
            if self.verbosity > 0:
                self.stdout.write("   Hospital {}: {}".format(obj.id,
                                                              serializer.data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding hospital data"))

            
    def seed_hospital_equipment_data(self, client):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital equipment data"))

        # seeding hospital 
        hospital_equipments = HospitalEquipment.objects.all()

        for obj in hospital_equipments:
            serializer = HospitalEquipmentSerializer(obj)
            client.update_topic('hospital/{}/equipment/{}/data'.format(obj.hospital.id,
                                                                       obj.equipment.name),
                                serializer,
                                qos=2,
                                retain=True)
            
            if self.verbosity > 0:
                self.stdout.write("   Hospital Equipment {}: {}".format(obj.id,
                                                                        serializer.data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding hospital equipment data"))

            
    def seed_hospital_metadata(self, client):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital metadata"))

        # seeding hospital metadata
        hospitals = Hospital.objects.all()

        for hospital in hospitals:
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            serializer = EquipmentSerializer(equipment, many=True)
            client.update_topic('hospital/{}/metadata'.format(hospital_id),
                                serializer,
                                qos=2,
                                retain=True)
            
            if self.verbosity > 0:
                self.stdout.write("   Hospital metadata {}: {}".format(hospital.id,
                                                                       serializer.data))

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Done seeding hospital metadata"))


    # Message publish callback
    def on_publish(self, client, userdata, mid):
        # make sure all is published before disconnecting
        self.pubcount -= 1
        # print("on_publish: '{}', '{}'".format(client, userdata))
        if self.pubcount == 0 and self.can_disconnect:
            self.disconnect()

class Command(BaseCommand):
    help = 'Seed the mqtt broker'

    def handle(self, *args, **options):

        import os

        broker = {
            'USERNAME': '',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLIENT_ID': 'django',
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'mqttseed_' + str(os.getpid())

        client = Client(broker, self.stdout, self.style,
                        verbosity = options['verbosity'])

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
