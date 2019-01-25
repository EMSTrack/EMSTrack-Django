import json
import logging
import time

from django.conf import settings
from django.utils import timezone

from ambulance.models import Ambulance, \
    AmbulanceStatus
from emstrack.tests.util import point2str
from equipment.models import EquipmentItem
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from mqtt.publish import SingletonPublishClient
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from .client import MQTTTestSubscribeClient as SubscribeClient

logger = logging.getLogger(__name__)


class TestMQTTPublish(TestMQTT, MQTTTestCase):

    def test(self):
        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=True)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topic = 'ambulance/{}/data'.format(self.a1.id)
        client.expect(topic)
        self.is_subscribed(client)

        # process messages
        self.loop(client)

        # Access singleton publish client
        publish_client = SingletonPublishClient()

        # disconnect temporarily
        publish_client.client.disconnect()
        self.is_disconnected(publish_client)

        # expect more ambulance
        client.expect(topic)

        # modify data in ambulance and save should trigger message
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)
        obj.status = AmbulanceStatus.OS.name
        obj.save()

        # save will trigger failed publish
        publish_client.buffer_lock.acquire()
        self.assertEqual(len(publish_client.buffer) > 0)
        publish_client.buffer_lock.release()

        # reconnect
        publish_client.client.reconnect()
        self.is_connected(publish_client)

        # process messages
        self.loop(client)
        client.wait()

        # assert change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)
