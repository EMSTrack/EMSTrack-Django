from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from login.permissions import cache_clear
from mqtt.publish_client import PublishClient

from ambulance.models import Ambulance, Call, CallStatus, AmbulanceCallStatus

from hospital.models import Hospital
from equipment.models import EquipmentItem, EquipmentHolder


class Client(PublishClient):

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        # initialize
        self.pubset = set()
        self.can_disconnect = False

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
        self.seed_equipment_data()
        self.seed_equipment_metadata()

        # Seed ambulances
        self.seed_ambulance_data()

        # Seed profiles
        self.seed_profile_data()

        # Seed calls
        self.seed_call_data()

        # Good to disconnect
        self.can_disconnect = True

    def publish(self, topic, message, *vargs, **kwargs):

        # increment pubcount then publish
        result = self.client.publish(topic, message, *vargs, **kwargs)
        self.pubset.add(result.mid)

        # echo if verbosity > 0
        if self.verbosity > 0:
            if message is None:
                op = '-'
            else:
                op = '+'
            if self.verbosity > 1:
                self.stdout.write("   {}{}: {}".format(op, topic, message))
            elif self.verbosity > 0:
                self.stdout.write("   {}{}".format(op, topic))

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

        # clear profile cache
        cache_clear()

        # seeding profiles
        for obj in User.objects.all():
            self.publish_profile(obj)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding profile data"))

    def seed_ambulance_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding vehicle data"))

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

    def seed_equipment_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding equipment data"))

        # seeding hospital 
        for obj in EquipmentItem.objects.all():
            self.publish_equipment_item(obj)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding equipment data"))

    def seed_equipment_metadata(self):
        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding equipment metadata"))

        # seeding hospital metadata
        for equipmentholder in EquipmentHolder.objects.all():
            self.publish_equipment_metadata(equipmentholder)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding equipment metadata"))

    def seed_call_data(self):

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS(">> Seeding call data"))

        # seeding ambulances
        for obj in Call.objects.all():

            # if call is not ended
            if obj.status != CallStatus.E.name:
                self.publish_call(obj)

                for ambulancecall in obj.ambulancecall_set.all():
                    if ambulancecall.status != AmbulanceCallStatus.C.name:
                        self.publish_call_status(ambulancecall)
                    else:
                        self.remove_call_status(ambulancecall)

            else:
                self.remove_call(obj)

        if self.verbosity > 0:
            self.stdout.write(self.style.SUCCESS("<< Done seeding call data"))

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
                        stdout=self.stdout,
                        style=self.style,
                        verbosity=options['verbosity'])

        try:
            client.loop_forever()

        except KeyboardInterrupt:
            pass

        finally:
            client.disconnect()
