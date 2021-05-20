import json

from django.conf import settings
from django.test import Client as DjangoClient
from mqtt.tests.client import TestMQTT, MQTTTestCase, MQTTTestSubscribeClient as SubscribeClient, MQTTTestClient

from login.models import ClientStatus, Client

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

        # start django client
        django_client = DjangoClient()

        # login as admin
        django_client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # handshake ambulance and hospital
        response = django_client.post('/en/api/client/',
                                      content_type='application/json',
                                      data=json.dumps({
                                          'client_id': client_id,
                                          'status': ClientStatus.O.name,
                                          'ambulance': self.a1.id,
                                          'hospital': self.h1.id
                                      }),
                                      follow=True)
        self.assertEqual(response.status_code, 201)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, self.a1)
        self.assertEqual(clnt.hospital, self.h1)
        
        # payload 
        payload = {
            'location': 'xyz',
            'status': 'alert', # alert, acknowledge 
            'id': 'ambulance 1',
        }    
        json_payload = json.dumps(payload)

        # expected message
        payload.update({'user': self.u1.username, 'client': client_id})
        expected_payload = json.dumps(payload)

        # subscribe to ambulance/+/panic
        test_client.expect('ambulance/{}/panic'.format(self.a1.id), expected_payload)
        self.is_subscribed(test_client)

        # Publish panic message
        publish_topic = 'user/{}/client/{}/ambulance/{}/panic'.format(self.u1.username, client_id, self.a1.id)
        test_client.publish(publish_topic, json_payload, qos=0)

        # process messages
        self.loop(test_client, subscribe_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)
        self.assertEqual(clnt.ambulance, None)
        self.assertEqual(clnt.hospital, None)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()
        django_client.logout()