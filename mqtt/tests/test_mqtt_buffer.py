import logging
import logging
import time

from django.conf import settings

from ambulance.models import Ambulance, \
    AmbulanceStatus
from mqtt.publish import SingletonPublishClient
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from mqtt.client import RETRY_TIMER_SECONDS

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
        self.assertTrue(len(publish_client.buffer) > 0)
        publish_client.buffer_lock.release()

        # reconnect
        publish_client.client.reconnect()
        self.is_connected(publish_client)

        # wait for timer to come alive
        time.sleep(3 * RETRY_TIMER_SECONDS)

        # make sure timer got called
        publish_client.buffer_lock.acquire()
        self.assertTrue(len(publish_client.buffer) == 0)
        publish_client.buffer_lock.release()

        # process messages
        self.loop(client)
        # client.wait()

        # assert change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)
