import logging
import logging
import time

from django.conf import settings

from ambulance.models import Ambulance, \
    AmbulanceStatus
from login.permissions import cache_clear, get_permissions, cache_info
from mqtt.publish import SingletonPublishClient
from mqtt.subscribe import SubscribeClient
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from mqtt.client import RETRY_TIMER_SECONDS

from .client import MQTTTestSubscribeClient as SubscribeClient

logger = logging.getLogger(__name__)


class TestMQTTTestCache(TestMQTT, MQTTTestCase):

    def test_cache(self):

        # clear cache
        cache_clear()

        # retrieve permissions for user u1
        get_permissions(self.u1)
        get_permissions(self.u1)
        get_permissions(self.u1)
        get_permissions(self.u1)
        info = cache_info()
        self.assertEqual(info.hits, 3)
        self.assertEqual(info.misses, 1)
        self.assertEqual(info.currsize, 1)

        # retrieve permissions for user u2 and u1
        get_permissions(self.u2)
        get_permissions(self.u1)
        get_permissions(self.u2)
        get_permissions(self.u1)
        info = cache_info()
        self.assertEqual(info.hits, 6)
        self.assertEqual(info.misses, 2)
        self.assertEqual(info.currsize, 2)


class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test(self):

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqttclient'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client

        broker.update(settings.MQTT)
        client_id = 'test_mqtt_subscribe_admin'
        username = broker['USERNAME']
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # send cache_clear
        test_client.publish('message', 'cache_clear')

        # process messages
        self.loop(test_client, subscribe_client)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()
