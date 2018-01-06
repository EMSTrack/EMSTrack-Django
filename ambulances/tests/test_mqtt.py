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

from ambulances.models import Profile, Ambulance, \
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
        
        print('\n>> Starting django server at {}'.format(cls.live_server_url))
        
        print('>> Stoping mosquitto')
        
        # stop mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "stop"])

        # saving persistence file
        retval = subprocess.run(["mv",
                                 "-f", 
                                 "/var/lib/mosquitto/mosquitto.db",
                                 "/var/lib/mosquitto/mosquitto.db.org"])
        
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
        
        super().tearDownClass()
        
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

        # restore persistence file
        retval = subprocess.run(["mv",
                                 "-f", 
                                 "/var/lib/mosquitto/mosquitto.db.org",
                                 "/var/lib/mosquitto/mosquitto.db"])
        
        print('>> Starting mosquitto')
        
        # start mosquito server
        retval = subprocess.run(["service",
                                 "mosquitto",
                                 "start"])
        
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
from ambulances.mqttclient import BaseClient, MQTTException
        
# MQTTTestClient
class MQTTTestClient(BaseClient):

    def __init__(self, *args, **kwargs):

        # call supper
        super().__init__(*args, **kwargs)

        # expect
        self.expecting_topics = {}
        self.expecting = 0

        # initialize pubcount
        self.pubset = set()

    def done(self):

        return len(self.pubset) == 0 and self.expecting == 0
        
    # The callback for when the client receives a CONNACK
    # response from the server.
    def on_connect(self, client, userdata, flags, rc):

        # is connected?
        return super().on_connect(client, userdata, flags, rc)

    # The callback for when a subscribed message is received from the server.
    def on_message(self, client, userdata, msg):

        if msg.topic in self.expecting_topics:

            # first time got topic
            if self.expecting_topics[msg.topic] == 0:
                self.expecting -= 1

            # add to count
            self.expecting_topics[msg.topic] += 1

            print('> topic = {}'.format(msg.topic))
            print('> topic count = {}'.format(self.expecting_topics[msg.topic]))
            print('> expecting = {}'.format(self.expecting))
            print('> done = {}'.format(self.done()))
            print('> connected = {}'.format(self.connected))
            
        else:
        
            raise Exception("Unexpected message topic '{}'".format(msg.topic))

    def expect(self, topic, msg, qos = 2, remove = False):

        if not topic in self.expecting_topics:
            self.expecting_topics[topic] = 0
            self.expecting += 1
            self.subscribe(topic, qos)
        
class TestMQTTSeed(LiveTestSetup):

    MAX_TRIES = 100
    
    def test_mqttseed(self):

        # seed
        from django.core import management
    
        management.call_command('mqttseed',
                                verbosity=1)
        
        # Start client as admin
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
        broker['CLIENT_ID'] = 'test_mqttseed_admin'
        
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        qos = 0
        
        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
                          qos)

        # Subscribed?
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        k = 0
        while not client.done()and k < self.MAX_TRIES:
            k += 1
            client.loop()
            
        self.assertEqual(client.done(), True)
        print('<< done')
        
        client.disconnect()

        # Repeat with same client
        
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
                          qos)

        # Subscribed?
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        k = 0
        while not client.done()and k < self.MAX_TRIES:
            k += 1
            client.loop()
            
        self.assertEqual(client.done(), True)
        print('<< done')
            
        client.disconnect()
        
        # Repeat with same client and different qos

        qos = 2
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        self.assertEqual(client.connected, True)
        
        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
                          qos)

        # Subscribed?
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        k = 0
        while not client.done()and k < self.MAX_TRIES:
            k += 1
            client.loop()
            
        self.assertEqual(client.done(), True)
        print('<< done')
            
        client.disconnect()

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1'

        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        self.assertEqual(client.connected, True)
        
        # Expect user profile
        profile = Profile.objects.get(user__username='testuser1')
        client.expect('user/testuser1/profile',
                      JSONRenderer().render(ExtendedProfileSerializer(profile).data),
                      qos)

        # Ambulances
        can_read = profile.ambulances.filter(can_read=True).values('ambulance_id')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)
        
        # Hospitals
        can_read = profile.hospitals.filter(can_read=True).values('hospital_id')
        for hospital in Hospital.objects.filter(id__in=can_read):
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            
        # Expect all hospital equipments
        for e in HospitalEquipment.objects.filter(hospital__id__in=can_read):
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Subscribed?
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        k = 0
        while not client.done()and k < self.MAX_TRIES:
            k += 1
            client.loop()
            
        self.assertEqual(client.done(), True)
        print('<< done')
            
        client.disconnect()
        
    def _test(self):

        print('<< testuser1')
        
            
        try:
        
            client.loop_start()
        
            while not client.connected or not client.done():
                print('connected = {}, done = {}'.format(client.connected,
                                                         client.done()))
                print('subscribed = {}'.format(client.subscribed))
                time.sleep(1)
            
            self.assertEqual(client.connected, True)

            client.loop_stop()
            
        except KeyboardInterrupt:
            pass
        
        finally:
            client.disconnect()

    def _test(self):
            
        # Start client as common user with wrong password
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secreto'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1_wrong'

        # with self.assertRaises():
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        with self.assertRaises(MQTTException) as cm:
            while True:
                client.loop()
        
        self.assertEqual(client.connected, False)
        self.assertEqual(cm.exception.value, 5)

        client.disconnect()
        
