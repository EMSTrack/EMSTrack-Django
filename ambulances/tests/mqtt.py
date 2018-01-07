import subprocess, time, os, sys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.conf import settings

from django.contrib.auth.models import User

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style, no_style
from ambulances.mqttclient import BaseClient, MQTTException
        
class MQTTTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):

        # Add admin user
        if not User.objects.get(username=settings.MQTT['USERNAME']):
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
        
