import logging
import os
import re
import subprocess
import time
import socket

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from ambulance.models import Ambulance, \
    AmbulanceCapability
from hospital.models import Hospital
from equipment.models import EquipmentType, Equipment, EquipmentItem
from login.models import GroupAmbulancePermission, GroupHospitalPermission, \
    UserAmbulancePermission, UserHospitalPermission
from mqtt.client import BaseClient
from mqtt.publish_client import SingletonPublishClient
from mqtt.subscribe import SubscribeClient

logger = logging.getLogger(__name__)


class MQTTTestCase(StaticLiveServerTestCase):

    mqtt_status = True

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

    @classmethod
    def run_until_success(cls, args, **kwargs):

        # parameters
        MAX_TRIES = kwargs.pop('MAX_TRIES', 10)
        
        # keep trying 
        k = 0
        success = False
        while not success and k < MAX_TRIES:
            if k > 0:
                time.sleep(1)
            k += 1
            retval = subprocess.run(args, **kwargs)
            success = retval.returncode == 0

        if not success:
            raise Exception('Did not succeed!')

    @classmethod
    def run_until_fail(cls, args, **kwargs):

        # parameters
        MAX_TRIES = kwargs.pop('MAX_TRIES', 10)
        
        # keep trying 
        k = 0
        success = True
        while success and k < MAX_TRIES:
            if k > 0:
                time.sleep(1)
            k += 1
            retval = subprocess.run(args, **kwargs)
            success = retval.returncode == 0

        if success:
            raise Exception('Did not fail!')
        
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
        # super().setUpClass()
        cls.port = 8001
        cls.host = socket.gethostbyname(socket.gethostname())
        # cls.allowed_host = 'emstrack'
        super(MQTTTestCase, cls).setUpClass()

        # determine server and port
        protocol, host, port = cls.live_server_url.split(':')
        host = host[2:]

        logging.info('\n>> Starting django server at {}'.format(cls.live_server_url))
        
        # set up test data
        cls.setUpTestData()

        if os.environ.get("DJANGO_ENABLE_MQTT_PUBLISH", "True") == "False":
            os.environ["DJANGO_ENABLE_MQTT_PUBLISH"] = "True"
            logger.info('> Enabling MQTT')

    @classmethod
    def tearDownClass(cls):

        # disconnect singleton publish client
        SingletonPublishClient().disconnect()

        # os.environ["DJANGO_ENABLE_MQTT_PUBLISH"] = "False"
        # logger.info('Disabling MQTT after testing')

        # call super to shutdown server
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):

        # Retrieve admin
        cls.u1 = User.objects.get(username=settings.MQTT['USERNAME'])

        try:
            
            # Add users
            cls.u2 = User.objects.get(username='testuser1')
            cls.u3 = User.objects.get(username='testuser2')
            cls.u4 = User.objects.get(username='testuser3')
            cls.u5 = User.objects.get(username='testuser4')
            cls.u6 = User.objects.get(username='highprioritytestuser')
            cls.u7 = User.objects.get(username='lowprioritytestuser')
            cls.u8 = User.objects.get(username='staff')

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
            cls.he1 = EquipmentItem.objects.get(equipmentholder=cls.h1.equipmentholder,
                                                equipment=cls.e1)
            
            cls.he2 = EquipmentItem.objects.get(equipmentholder=cls.h1.equipmentholder,
                                                equipment=cls.e2)

            cls.he3 = EquipmentItem.objects.get(equipmentholder=cls.h2.equipmentholder,
                                                equipment=cls.e1)
            
            cls.he4 = EquipmentItem.objects.get(equipmentholder=cls.h2.equipmentholder,
                                                equipment=cls.e3)
            
            cls.he5 = EquipmentItem.objects.get(equipmentholder=cls.h3.equipmentholder,
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

            cls.u4 = User.objects.create_user(
                username='testuser3',
                email='test3@user.com',
                password='highly_secret')

            cls.u5 = User.objects.create_user(
                username='testuser4',
                email='test4@user.com',
                password='extremely_secret')

            cls.u6 = User.objects.create_user(
                username='highprioritytestuser',
                email='test6@user.com',
                password='exceptionally_secret')

            cls.u7 = User.objects.create_user(
                username='lowprioritytestuser',
                email='test7@user.com',
                password='exceedingly_secret')

            cls.u8 = User.objects.create_user(
                username='staff',
                email='staff@user.com',
                password='so_secret',
                is_staff=True)

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
                number="1234",
                street="don't know",
                comment="no comments",
                updated_by=cls.u1)
            
            cls.h2 = Hospital.objects.create(
                name='Hospital CruzRoja',
                number="4321",
                street='Forgot',
                updated_by=cls.u1)
            
            cls.h3 = Hospital.objects.create(
                name='Hospital Nuevo',
                number="0000",
                street='Not built yet',
                updated_by=cls.u1)
            
            # add equipment
            cls.e1 = Equipment.objects.create(
                name='X-ray',
                type=EquipmentType.B.name)
            
            cls.e2 = Equipment.objects.create(
                name='Beds',
                type=EquipmentType.I.name)
            
            cls.e3 = Equipment.objects.create(
                name='MRI - Ressonance',     # name with space!
                type=EquipmentType.B.name)
            
            # add hospital equipment
            cls.he1 = EquipmentItem.objects.create(
                equipmentholder=cls.h1.equipmentholder,
                equipment=cls.e1,
                value='True',
                updated_by=cls.u1)
            
            cls.he2 = EquipmentItem.objects.create(
                equipmentholder=cls.h1.equipmentholder,
                equipment=cls.e2,
                value='45',
                updated_by=cls.u1)

            cls.he3 = EquipmentItem.objects.create(
                equipmentholder=cls.h2.equipmentholder,
                equipment=cls.e1,
                value='False',
                updated_by=cls.u1)
            
            cls.he4 = EquipmentItem.objects.create(
                equipmentholder=cls.h2.equipmentholder,
                equipment=cls.e3,
                value='True',
                updated_by=cls.u1)
            
            cls.he5 = EquipmentItem.objects.create(
                equipmentholder=cls.h3.equipmentholder,
                equipment=cls.e1,
                value='True',
                updated_by=cls.u1)

            # add hospitals to users
            UserHospitalPermission.objects.create(user=cls.u2,
                                                  hospital=cls.h1,
                                                  can_write=True)
            UserHospitalPermission.objects.create(user=cls.u2,
                                                  hospital=cls.h3)

            UserHospitalPermission.objects.create(user=cls.u3,
                                                  hospital=cls.h1)
            UserHospitalPermission.objects.create(user=cls.u3,
                                                  hospital=cls.h2,
                                                  can_write=True)

            # u3 has no hospitals

            # add ambulances to users
            UserAmbulancePermission.objects.create(user=cls.u1,
                                                   ambulance=cls.a2,
                                                   can_write=True)

            # u2 has no ambulances

            UserAmbulancePermission.objects.create(user=cls.u3,
                                                   ambulance=cls.a1,
                                                   can_read=False)
            UserAmbulancePermission.objects.create(user=cls.u3,
                                                   ambulance=cls.a3,
                                                   can_write=True)

            # Create groups
            cls.g1 = Group.objects.create(name='EMTs')
            cls.g2 = Group.objects.create(name='Drivers')
            cls.g3 = Group.objects.create(name='Dispatcher')

            # add hospitals to groups
            GroupHospitalPermission.objects.create(group=cls.g1,
                                                   hospital=cls.h1,
                                                   can_write=True)
            GroupHospitalPermission.objects.create(group=cls.g1,
                                                   hospital=cls.h3)

            GroupHospitalPermission.objects.create(group=cls.g2,
                                                   hospital=cls.h1)
            GroupHospitalPermission.objects.create(group=cls.g2,
                                                   hospital=cls.h2,
                                                   can_write=True)

            # g3 has no hospitals

            # add ambulances to groups
            GroupAmbulancePermission.objects.create(group=cls.g1,
                                                    ambulance=cls.a2,
                                                    can_write=True)

            # g2 has no ambulances

            GroupAmbulancePermission.objects.create(group=cls.g3,
                                                    ambulance=cls.a1,
                                                    can_read=False)
            GroupAmbulancePermission.objects.create(group=cls.g3,
                                                    ambulance=cls.a3,
                                                    can_write=True)

            cls.u4.groups.set([cls.g2])
            cls.u5.groups.set([cls.g1, cls.g3])


class MQTTTestClientPublishSubscribeMixin:

    def __init__(self, *args, **kwargs):

        # call supper
        super().__init__(*args, **kwargs)

        # publishing and subscribing
        self.publishing = 0
        self.subscribing = 0

    def has_published(self):
        return self.publishing == 0

    def has_subscribed(self):
        return self.subscribing == 0

    def done(self):
        return self.has_published() and self.has_subscribed()

    def publish(self, topic, payload=None, qos=0, retain=False):

        # publish
        self.publishing += 1
        if self.debug:
            logger.debug("Publishing to '{}', publishing={}".format(topic, self.publishing))

        super().publish(topic, payload, qos, retain)

    def on_publish(self, client, userdata, mid):

        # did publish?
        super().on_publish(client, userdata, mid)
        self.publishing -= 1

        if self.debug:
            logger.debug("Just published mid={}, publishing={}]".format(mid, self.publishing))

    def subscribe(self, topic, qos=0):

        # publish
        self.subscribing += 1
        if self.debug:
            logger.debug("Subscribing to '{}', subscribing={}".format(topic, self.subscribing))

        super().subscribe(topic, qos)

    def on_subscribe(self, client, userdata, mid, granted_qos):

        # did subscribe?
        super().on_subscribe(client, userdata, mid, granted_qos)
        self.subscribing -= 1

        if self.debug:
            logger.debug('Just subscribed mid={}, qos={}, subscribing={}'.format(mid, granted_qos, self.subscribing))


class MQTTTestSubscribeClient(MQTTTestClientPublishSubscribeMixin,
                              SubscribeClient):

    def __init__(self, *args, **kwargs):

        # call supper
        super().__init__(*args, **kwargs)


# MQTTTestClient
class MQTTTestClient(MQTTTestClientPublishSubscribeMixin,
                     BaseClient):

    def __init__(self, *args, **kwargs):

        self.check_payload = kwargs.pop('check_payload', True)
        
        # call supper
        super().__init__(*args, **kwargs)

        # expect
        self.expecting_topics = {}
        self.expecting_messages = {}
        self.expecting_patterns = {}
        self.expecting = 0

    def is_expecting(self):
        return self.expecting > 0

    def done(self):
        return super().done() and not self.is_expecting()

    # The callback for when a subscribed message is received from the server.
    def on_message(self, client, userdata, msg):

        if msg.topic in self.expecting_topics:

            # regular topic
            topic = msg.topic

        else:
            
            # can it be a pattern?
            match = False
            for k, p in self.expecting_patterns.items():
                if p.match(msg.topic):
                    # initialize topic
                    topic = k
                    match = True
                    break

            if not match:
                # did not match
                raise Exception("Unexpected message topic '{}'".format(msg.topic))

        # handle expected message
        self.expecting_topics[topic] += 1
        self.expecting -= 1

        # is message payload expected? remove
        try:
                
            self.expecting_messages[topic].remove(msg.payload)

        except ValueError:

            if self.check_payload:
                raise Exception('Unexpected message "{}:{}"'.format(msg.topic, msg.payload))

        if self.debug:
            logger.debug('Just received {}[count={},expecting={}]:{}'.format(msg.topic,
                                                                             self.expecting_topics[topic],
                                                                             self.expecting,
                                                                             msg.payload))

    def expect(self, topic, msg=None, qos=2):

        # not subscribed
        if topic not in self.expecting_topics:

            # pattern topic?
            if '+' in topic or '#' in topic:
                pattern = topic.replace('+', '[^/]+').replace('#', '[a-zA-Z0-9_/ ]+')
                self.expecting_patterns[topic] = re.compile(pattern)
                # print('pattern = {}'.format(pattern))

            # initialize
            self.expecting_topics[topic] = 0
            self.expecting_messages[topic] = []

            # and subscribe
            self.subscribe(topic, qos)

        else:

            logger.debug("Already subscribed to topic '{}'".format(topic))

        self.expecting += 1
        self.expecting_messages[topic].append(msg)


class TestMQTT:

    DELAY = 0.1

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

    def is_connected(self, client, max_tries=10):

        # loop
        client.loop()

        # connected?
        k = 0
        while (not client.is_connected()) and k < max_tries:
            k += 1
            client.loop()
            time.sleep(TestMQTT.DELAY)

        self.assertEqual(client.is_connected(), True)

    def is_disconnected(self, client, max_tries=10):

        # loop
        client.loop()

        # disconnected?
        k = 0
        while (client.is_connected()) and k < max_tries:
            k += 1
            client.loop()
            time.sleep(TestMQTT.DELAY)

        self.assertEqual(client.is_connected(), False)

    def is_subscribed(self, client, max_tries=10):

        # loop
        client.loop()

        # client.loop_start()

        # connected?
        k = 0
        while (not client.has_subscribed()) and k < max_tries:
            k += 1
            client.loop()
            time.sleep(TestMQTT.DELAY)

        # client.loop_stop()

        logger.debug('has_subscribed = {}, k = {}'.format(client.has_subscribed(), k))

        self.assertEqual(client.has_subscribed(), True)

    def loop(self, *clients, max_tries=10):

        # logger.debug('clients = {}'.format(clients))
        # logger.debug('MAX_TRIES = {}'.format(MAX_TRIES))

        # starts clients
        for client in clients:
            client.loop()

        # connected?
        k = 0
        done = False
        while not done and k < max_tries:
            done = True
            for client in clients:
                done = done and client.done()
            k += 1
            # stop clients
            for client in clients:
                client.loop()
            time.sleep(TestMQTT.DELAY)

        if not done:
            # logger.debug('NOT DONE:')
            for client in clients:
                if hasattr(client, 'expecting'):
                    logger.debug('expecting = {}'.format(client.expecting))
                if hasattr(client, 'publishing'):
                    logger.debug('publishing = {}'.format(client.publishing))
                if hasattr(client, 'subscribing'):
                    logger.debug('subscribing= {}'.format(client.subscribing))

        self.assertEqual(done, True)
