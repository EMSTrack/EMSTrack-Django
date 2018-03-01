# mqttseed application command
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.six import BytesIO

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from mqtt.publish import PublishClient

from django.contrib.auth.models import User

from login.models import UserProfile
    
from ambulance.models import Ambulance

from hospital.models import Hospital, HospitalEquipment

class Client(PublishClient):

    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

        # initialize pubset
        self.pubset = set()
        self.can_disconnect = False

        # Seed settings
        self.seed_settings()
        
        # Seed hospitals
        self.seed_hospital_data()
        self.seed_hospital_equipment_data()
        self.seed_hospital_metadata()

        # Seed ambulances
        self.seed_ambulance_data()

        # Seed profiles
        self.seed_profile_data()
        
        # Seed calls
        # self.seed_calls()

        # Good to disconnect
        self.can_disconnect = True
        
    def publish(self, topic, message, *vargs, **kwargs):

        # increment pubcount then publish
        result = self.client.publish(topic, message, *vargs, **kwargs)
        self.pubset.add(result.mid)

        # echo if verbosity > 0
        if self.verbosity > 1:
            self.stdout.write("   {}: {}".format(topic, message))
        elif self.verbosity > 0:
            self.stdout.write("   {}".format(topic))

    def seed_settings(self):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding settings"))

        # seeding settings
        self.publish_settings()
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding settings"))
            
    def seed_profile_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding profile data"))

        # seeding profiles
        for obj in User.objects.all():
            self.publish_profile(obj)
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding profile data"))
            
    def seed_ambulance_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding ambulance data"))

        # seeding ambulances
        for obj in Ambulance.objects.all():
            self.publish_ambulance(obj)
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding ambulance data"))

    def seed_hospital_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital data"))

        # seeding hospital 
        for obj in Hospital.objects.all():
            self.publish_hospital(obj)
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding hospital data"))

            
    def seed_hospital_equipment_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital equipment data"))

        # seeding hospital 
        for obj in HospitalEquipment.objects.all():
            self.publish_hospital_equipment(obj)
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding hospital equipment data"))

            
    def seed_hospital_metadata(self):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding hospital metadata"))

        # seeding hospital metadata
        for hospital in Hospital.objects.all():
            self.publish_hospital_metadata(hospital)
            
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding hospital metadata"))


    # Message publish callback
    def on_publish(self, client, userdata, mid):

        # make sure all is published before disconnecting
        self.pubset.remove(mid)
        if len(self.pubset) == 0 and self.can_disconnect:
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

        client = Client(broker,
                        stdout = self.stdout,
                        style = self.style,
                        verbosity = options['verbosity'])

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
