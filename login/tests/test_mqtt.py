import subprocess, time, os, sys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings

from django.contrib.auth.models import User

from ambulances.models import Hospital, HospitalPermission

from django.test import Client

from ..views import LoginView, SignupView, LogoutView, MQTTLoginView, MQTTSuperuserView, MQTTAclView

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
        
        # Add hospitals
        cls.h1 = Hospital.objects.create(name='hospital1',
                                          address='somewhere',
                                          updated_by=cls.u1)
        cls.h2 = Hospital.objects.create(name='hospital2',
                                          address='somewhere else',
                                          updated_by=cls.u1)
        cls.h3 = Hospital.objects.create(name='hospital3',
                                          address='somewhere other',
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

class TestMQTTAuth(LiveTestSetup):

    def test_mqtt_login(self):

        print('hi')
        
    def _test(self):
        
        # instantiate client
        client = Client()
        
        # blank login
        response = client.get('/aauth/mqtt/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser11',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser11' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect password
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # correct login
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

        # login user2
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser2',
                                 'password': 'very_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser2' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # login admin
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'admin',
                                 'password': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

    def _test_mqtt_acl_publish(self):
        
        # instantiate client
        client = Client()

        # login
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # not super
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/hospital' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/ambulance' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/location' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/llocation' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong user in topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser2/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # super behaves the same because it never gets acl tested
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/hospital' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/ambulance' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/location' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/llocation' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong user in topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser2/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'admin',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

    def _test_mqtt_acl_subscribe(self):
        
        # instantiate client
        client = Client()
        
        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/user/testuser1/hospitals' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/hospitals' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h1.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h3.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h2.id) },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/rx'.format(self.h1.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/beds'.format(self.h3.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/rx'.format(self.h2.id) },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can subscribe
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/user/testuser1/ambulances' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
