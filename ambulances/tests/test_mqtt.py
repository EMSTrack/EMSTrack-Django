import subprocess, time, os, sys

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings

from rest_framework.renderers import JSONRenderer

from rest_framework import serializers

from ambulances.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability, \
    AmbulancePermission, HospitalPermission, \
    Hospital, \
    Equipment, HospitalEquipment, EquipmentType

from ambulances.serializers import ProfileSerializer, \
    AmbulanceSerializer, ExtendedProfileSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer, \
    EquipmentSerializer

from django.test import Client

def date2iso(date):
    if date is not None:
        return date.isoformat().replace('+00:00','Z')
    return date

def point2str(point):
    #return 'SRID=4326;' + str(point)
    if point is not None:
        return str(point)
    return point

class LiveTestSetup(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):

        # Add admin user
        cls.u1 = User.objects.create_user(
            username=settings.MQTT['USERNAME'],
            email='admin@user.com',
            password=settings.MQTT['PASSWORD'],
            is_superuser=True)
        
        # Create server
        super().setUpClass()

        # determine server and port
        protocol, host, port = cls.live_server_url.split(':')
        host = host[2:]
        
        print('\n>> Starting django server at {}, {}:{}'.format(cls.live_server_url, host, port))
        

        print('>> Stoping mosquitto')
        
        # stop mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "stop"])

        # create test configuration file
        with open('/etc/mosquitto/conf.d/test.conf', "w") as outfile:
            
            # change default host and port
            cat = subprocess.Popen(["cat",
                                    "/etc/mosquitto/conf.d/default.conf"],
                                   stdout= subprocess.PIPE)
            sed = subprocess.run(["sed",
                                  "s/8000/{}/".format(port)],
                                 stdin=cat.stdout,
                                 stdout=outfile)
            
        # move current configuration file
        retval = subprocess.run(["mv",
                                 "/etc/mosquitto/conf.d/default.conf",
                                 "/etc/mosquitto/conf.d/default.conf.org"])

        print('>> Start mosquitto with test settings')

        # start mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "start"])

        cls.setUpTestData()

    @classmethod
    def tearDownClass(cls):
        
        print('>> Stopping mosquitto with test settings')
        
        # stop mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "stop"])
        
        # remove test configuration file
        retval = subprocess.run(["mv",
                                 "/etc/mosquitto/conf.d/test.conf",
                                 "/etc/mosquitto/conf.d/test.conf.org"])
        
        # restore current configuration file
        retval = subprocess.run(["mv",
                                 "/etc/mosquitto/conf.d/default.conf.org",
                                 "/etc/mosquitto/conf.d/default.conf"])

        print('>> Starting mosquitto')
        
        # start mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "start"])
        
        super().tearDownClass()
        
    @classmethod
    def setUpTestData(cls):

        # Add users
        cls.u2 = User.objects.create_user(
            username='testuser1',
            email='test1@user.com',
            password='top_secret')
        
        cls.u3 = User.objects.create_user(
            username='testuser2',
            email='test2@user.com',
            password='very_secret')
        
        # Add ambulances
        cls.a1 = Ambulance.objects.create(
            identifier='BC-179',
            comment='Maintenance due',
            capability=AmbulanceCapability.B.name,
            updated_by=cls.u1)
        
        cls.a2 = Ambulance.objects.create(
            identifier='BC-180',
            comment='Need painting',
            capability=AmbulanceCapability.A.name,
            updated_by=cls.u1)

        cls.a3 = Ambulance.objects.create(
            identifier='BC-181',
            comment='Engine overhaul',
            capability=AmbulanceCapability.R.name,
            updated_by=cls.u1)
        
        # Add hospitals
        cls.h1 = Hospital.objects.create(
            name='Hospital General',
            address="Don't know",
            comment="no comments",
            updated_by=cls.u1)
        
        cls.h2 = Hospital.objects.create(
            name='Hospital CruzRoja',
            address='Forgot',
            updated_by=cls.u1)

        cls.h3 = Hospital.objects.create(
            name='Hospital Nuevo',
            address='Not built yet',
            updated_by=cls.u1)

        # add equipment
        cls.e1 = Equipment.objects.create(
            name='X-ray',
            etype=EquipmentType.B.name)

        cls.e2 = Equipment.objects.create(
            name='Beds',
            etype=EquipmentType.I.name)
        
        cls.e3 = Equipment.objects.create(
            name='MRI - Ressonance',     # name with space!
            etype=EquipmentType.B.name,
            toggleable=True)

        # add hospital equipment
        cls.he1 = HospitalEquipment.objects.create(
            hospital=cls.h1,
            equipment=cls.e1,
            value='True',
            updated_by=cls.u1)
        
        cls.he2 = HospitalEquipment.objects.create(
            hospital=cls.h1,
            equipment=cls.e2,
            value='45',
            updated_by=cls.u1)

        cls.he3 = HospitalEquipment.objects.create(
            hospital=cls.h2,
            equipment=cls.e1,
            value='False',
            updated_by=cls.u1)
        
        cls.he4 = HospitalEquipment.objects.create(
            hospital=cls.h2,
            equipment=cls.e3,
            value='True',
            updated_by=cls.u1)
        
        cls.he5 = HospitalEquipment.objects.create(
            hospital=cls.h3,
            equipment=cls.e1,
            value='True',
            updated_by=cls.u1)
        
        # add hospitals to users
        cls.u1.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=cls.h1,
                                              can_write=True),
            HospitalPermission.objects.create(hospital=cls.h3)
        )
        
        cls.u2.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=cls.h1),
            HospitalPermission.objects.create(hospital=cls.h2,
                                              can_write=True)
        )

        # u3 has no hospitals 
        
        # add ambulances to users
        cls.u1.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=cls.a2,
                                               can_write=True)
        )
        
        # u2 has no ambulances
        
        cls.u3.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=cls.a1,
                                               can_read=False),
            AmbulancePermission.objects.create(ambulance=cls.a3,
                                               can_write=True)
        )

        #print('u1: {}\n{}'.format(cls.u1, cls.u1.profile))
        #print('u2: {}\n{}'.format(cls.u2, cls.u2.profile))
        #print('u3: {}\n{}'.format(cls.u3, cls.u3.profile))


from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style
from ambulances.mqttclient import BaseClient
        
# MQTTTestClient
class MQTTTestClient(BaseClient):

    def __init__(self, *args, **kwargs):

        # call supper
        super().__init__(*args, **kwargs)

        # expect
        self.expecting = {}

        # initialize pubcount
        self.pubset = set()

    def done(self):

        return len(self.pubset) == 0 and len(self.expecting) == 0
        
    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        if not super().on_connect(client, userdata, flags, rc):
            return False

    # The callback for when a subscribed message is received from the server.
    def on_message(self, client, userdata, msg):

        if msg.topic in self.expecting:

            # pop from expected list
            expect = self.expecting[msg.topic].pop(0)
            value = msg.payload

            # remove topic if empty list
            if not self.expecting[msg.topic]:
                del self.expecting[msg.topic]

            # assert content
            self.test.assertEqual(value, expect)

        else:
        
            raise Exception("Unexpected message topic '{}'".format(msg.topic))

        # disconnect
        if self.done():
            self.disconnect()
            
    def expect(self, topic, msg):

        if topic in self.expecting:
            self.expecting[topic].append(msg)
        else:
            self.expecting[topic] = [msg]
            self.client.subscribe(topic, 2)
        
class TestMQTTSeed(LiveTestSetup):
        
    def test_mqttseed(self):

        # seed
        from django.core import management
    
        management.call_command('mqttseed',
                                verbosity=2)
        
        # Start client
        stdout = OutputWrapper(sys.stdout)
        style = color_style()

        # Instantiate broker
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqttseed'
        
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self
        
        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data))

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data))
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment).data))

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data))

        # subscribe to all just in case
        client.subscribe('#',2)
            
        try:
        
            client.loop_start()
        
            while not client.done():
                time.sleep(1)
            
            client.loop_stop()
            
        except KeyboardInterrupt:
            pass
        
        finally:
            client.disconnect()
        
