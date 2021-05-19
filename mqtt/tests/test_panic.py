import json

from django.conf import settings
from mqtt.tests.client import TestMQTT, MQTTTestCase, MQTTTestSubscribeClient as SubscribeClient, MQTTTestClient

'''
    High-level idea:
    1.  a "mobile" client will publish to "/user/{user-id}/clinet/{client-id}/ambulance/{ambulance-id}/panic"
        with a payload specifying a panic i.e. { type: "panic", ...}
    2.  subscribe client will recieve message, parse it, and publish it to "ambulance/{ambulance-id}/panic"
    3.  a "website" client will be subscribed to "ambulance/+/panic"
    4. "website" client will receive message from subscribe client and use the message to generate popup
'''

class TestPanicPublish(TestMQTT, MQTTTestCase):

    def test_panic(self):
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'panic_subscribe_1'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client
        broker.update(settings.MQTT)
        client_id = 'panic_subscribe_2'
        username = broker['USERNAME']
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # subscribe to ambulance/+/panic
        test_client.expect('ambulance/{}/panic'.format(self.a1.id))
        self.is_subscribed(test_client)

        # Publish panic message
        publish_topic = 'user/{}/client/{}/ambulance/{}/panic'.format(self.u1.username, client_id, self.a1.id)
        publish_payload = json.dumps({
            'location': 'xyz',
            'id': 'ambulance 1',
        })
        test_client.publish(publish_topic, publish_payload, qos=0)

        # process messages
        self.loop(test_client, subscribe_client)