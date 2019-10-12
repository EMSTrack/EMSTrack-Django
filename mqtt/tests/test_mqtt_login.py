import logging

from django.conf import settings

from .client import MQTTTestCase, MQTTTestClient, TestMQTT

logger = logging.getLogger(__name__)


class TestMQTTConnect(TestMQTT, MQTTTestCase):

    def test_connect(self):
        # Start client as admin
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_login_1'

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
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_login_2'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        client.wait()

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        client.wait()

        # Start client as common user
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'

        client = MQTTTestClient(broker,
                                check_payload=False)

        self.is_connected(client)

        client.wait()
