from django.conf import settings
from mqtt.tests.client import TestMQTT, MQTTTestCase, MQTTTestClient


class TestPanicPublish(TestMQTT, MQTTTestCase):
    '''
        High-level idea:
        1.  a "mobile" client will publish to "/user/{user-id}/clinet/{client-id}/ambulance/{ambulance-id}/panic"
            with a payload specifying a panic i.e. { type: "panic", ...}
        2.  subscribe client will recieve message, parse it, and publish it to "ambulance/{ambulance-id}/panic"
        3.  a "website" client will be subscribed to "ambulance/+/panic"
        4. "website" client will receive message from subscribe client and use the message to generate popup
    '''

