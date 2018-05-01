from django.conf import settings

from ambulance.models import Ambulance, AmbulanceStatus
from mqtt.tests.client import MQTTTestCase, MQTTTestClient, TestMQTT


class TestMQTTSubscribe(MQTTTestCase):

    def test(self):

        self.assertTrue(True)


class TestMQTTPublish(TestMQTT, MQTTTestCase):

    def test(self):
        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 8884,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'

        client = MQTTTestClient(broker,
                                transport='websockets',
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topics = ('ambulance/{}/data'.format(self.a1.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                         self.e1.id))
        [client.expect(t) for t in topics]
        self.is_subscribed(client)

        # process messages
        self.loop(client)

        # expect more ambulance
        client.expect(topics[0])

        # modify data in ambulance and save should trigger message
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)
        obj.status = AmbulanceStatus.OS.name
        obj.save()

        # process messages
        self.loop(client)

        # assert change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)

        # Done?
        self.loop(client)
        client.wait()
