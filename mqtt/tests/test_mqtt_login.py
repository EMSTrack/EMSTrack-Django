import logging
import logging
import time

from django.conf import settings

from ambulance.models import Ambulance, \
    AmbulanceStatus
from login.tests.test_login import MyTestCase
from mqtt.publish import SingletonPublishClient
from mqtt.tests.client import MQTTTestClient
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from mqtt.client import RETRY_TIMER_SECONDS

logger = logging.getLogger(__name__)


class TestMQTTConnect(TestMQTT, MQTTTestCase):

    def test_connect(self):
        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_connect_admin'

        self.is_connected(MQTTTestClient(broker))

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'

        self.is_connected(MQTTTestClient(broker))

        # Start client as common user
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'

        self.is_connected(MQTTTestClient(broker))

        # wrong username
        broker['USERNAME'] = 'testuser22'
        broker['PASSWORD'] = 'very_secret'

        with self.assertRaises(AssertionError):
            self.is_connected(MQTTTestClient(broker))

        # wrong password
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secreto'

        with self.assertRaises(AssertionError):
            self.is_connected(MQTTTestClient(broker))


class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test_subscribe(self):

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_subscribe_admin'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        # subscribe to topics
        client.expect('user/{}/error'.format(broker['USERNAME']))
        client.expect('settings')
        client.expect('user/{}/profile'.format(broker['USERNAME']))
        self.is_subscribed(client)

        client.expect('ambulance/{}/data'.format(self.a1.id))
        client.expect('ambulance/{}/data'.format(self.a2.id))
        client.expect('ambulance/{}/data'.format(self.a3.id))
        self.is_subscribed(client)

        client.expect('hospital/{}/data'.format(self.h1.id))
        client.expect('hospital/{}/data'.format(self.h2.id))
        client.expect('hospital/{}/data'.format(self.h3.id))
        self.is_subscribed(client)

        client.expect('equipment/{}/item/+/data'.format(self.h1.id))
        client.expect('equipment/{}/item/+/data'.format(self.h2.id))
        client.expect('equipment/{}/item/+/data'.format(self.h3.id))
        self.is_subscribed(client)

        client.wait()

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        # subscribe to topics
        client.expect('user/{}/error'.format(broker['USERNAME']))
        client.expect('settings')
        client.expect('user/{}/profile'.format(broker['USERNAME']))
        self.is_subscribed(client)

        client.expect('ambulance/{}/data'.format(self.a1.id))
        client.expect('ambulance/{}/data'.format(self.a2.id))
        client.expect('ambulance/{}/data'.format(self.a3.id))
        self.is_subscribed(client)

        client.expect('hospital/{}/data'.format(self.h1.id))
        client.expect('hospital/{}/data'.format(self.h2.id))
        client.expect('hospital/{}/data'.format(self.h3.id))
        self.is_subscribed(client)

        client.expect('equipment/{}/item/+/data'.format(self.h1.id))
        client.expect('equipment/{}/item/+/data'.format(self.h2.id))
        client.expect('equipment/{}/item/+/data'.format(self.h3.id))
        self.is_subscribed(client)

        # client doesn't know it cannot subscribe to certain topics!
        # full testing in test_mqtt
        self.is_subscribed(client)

        client.wait()

        # Start client as common user
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        # subscribe to topics
        client.expect('user/{}/error'.format(broker['USERNAME']))
        client.expect('settings')
        client.expect('user/{}/profile'.format(broker['USERNAME']))
        self.is_subscribed(client)

        client.expect('ambulance/{}/data'.format(self.a1.id))
        client.expect('ambulance/{}/data'.format(self.a2.id))
        client.expect('ambulance/{}/data'.format(self.a3.id))
        self.is_subscribed(client)

        client.expect('hospital/{}/data'.format(self.h1.id))
        client.expect('hospital/{}/data'.format(self.h2.id))
        client.expect('hospital/{}/data'.format(self.h3.id))
        self.is_subscribed(client)

        client.expect('equipment/{}/item/+/data'.format(self.h1.id))
        client.expect('equipment/{}/item/+/data'.format(self.h2.id))
        client.expect('equipment/{}/item/+/data'.format(self.h3.id))
        self.is_subscribed(client)

        # client doesn't know it cannot subscribe to certain topics!
        # full testing in test_mqtt
        self.is_subscribed(client)
        client.wait()
