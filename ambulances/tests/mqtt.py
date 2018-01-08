import subprocess, time, os, sys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.conf import settings

from django.contrib.auth.models import User

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style
from ambulances.mqttclient import BaseClient, MQTTException

from ambulances.models import Profile, Ambulance, \
    AmbulanceStatus, AmbulanceCapability, \
    AmbulancePermission, HospitalPermission, \
    Hospital, \
    Equipment, HospitalEquipment, EquipmentType

class MQTTTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):

        try:

            # can get user?
            User.objects.get(username=settings.MQTT['USERNAME'])

        except:

            # Add admin user
            User.objects.create_user(
                username=settings.MQTT['USERNAME'],
                email='admin@user.com',
                password=settings.MQTT['PASSWORD'],
                is_superuser=True)
        
        # call super to create server
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

        # call super to shutdown server
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

        # Retrieve admin
        cls.u1 = User.objects.get(username=settings.MQTT['USERNAME'])

        try:
            
            # Add users
            cls.u2 = User.objects.get(username='testuser1')
            cls.u3 = User.objects.get(username='testuser2')

            # Add ambulances
            cls.a1 = Ambulance.objects.get(identifier='BC-179')
            cls.a2 = Ambulance.objects.get(identifier='BC-180')
            cls.a3 = Ambulance.objects.get(identifier='BC-181')

            # Add hospitals
            cls.h1 = Hospital.objects.get(name='Hospital General')
            cls.h2 = Hospital.objects.get(name='Hospital CruzRoja')
            cls.h3 = Hospital.objects.get(name='Hospital Nuevo')

            # Add equipment
            cls.e1 = Equipment.objects.get(name='X-ray')
            cls.e2 = Equipment.objects.get(name='Beds')
            cls.e3 = Equipment.objects.get(name='MRI - Ressonance')
            
            # add hospital equipment
            cls.he1 = HospitalEquipment.objects.get(hospital=cls.h1,
                                                    equipment=cls.e1)
            
            cls.he2 = HospitalEquipment.objects.get(hospital=cls.h1,
                                                    equipment=cls.e2)

            cls.he3 = HospitalEquipment.objects.get(hospital=cls.h2,
                                                    equipment=cls.e1)
            
            cls.he4 = HospitalEquipment.objects.get(hospital=cls.h2,
                                                    equipment=cls.e3)
            
            cls.he5 = HospitalEquipment.objects.get(hospital=cls.h3,
                                                    equipment=cls.e1)

            
        except:

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
            
            # Add permissions
            cls.u2.profile.hospitals.add(
                HospitalPermission.objects.create(hospital=cls.h1,
                                                  can_write=True),
                HospitalPermission.objects.create(hospital=cls.h3)
            )
            
            cls.u3.profile.hospitals.add(
                HospitalPermission.objects.create(hospital=cls.h1),
                HospitalPermission.objects.create(hospital=cls.h2,
                                                  can_write=True)
            )

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

    def expect(self, topic, msg = None, qos = 2, remove = False):

        if not topic in self.expecting_topics:
            self.expecting_topics[topic] = 0
            self.expecting += 1
            self.subscribe(topic, qos)
        
