import json
import ssl

from django.conf import settings
from django.test import Client as DjangoClient

from ambulance.models import Ambulance, AmbulanceStatus
from equipment.models import EquipmentItem
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from mqtt.publish import SingletonPublishClient
from mqtt.tests.client import MQTTTestCase, MQTTTestClient, TestMQTT
from .client import MQTTTestSubscribeClient as SubscribeClient


class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test(self):

        # Make sure publish client is looped
        SingletonPublishClient().loop()

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_websocket_test_mqtt_subscribe'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client over websockets
        broker.update(settings.MQTT)
        client_id = 'test_websocket_mqtt_test_mqtt_subscribe_admin'
        username = broker['USERNAME']

        broker['CLIENT_ID'] = client_id
        broker['PORT'] = 8884

        test_client = MQTTTestClient(broker,
                                     transport='websockets',
                                     tls_set={'ca_certs': None,
                                              'cert_reqs': ssl.CERT_NONE},
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # start django client
        django_client = DjangoClient()

        # login as admin
        django_client.login(username=broker['USERNAME'], password=broker['PASSWORD'])

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

        # Modify ambulance

        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        # publish change
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username,
                                                                         client_id,
                                                                         self.a1.id),
                            json.dumps({
                                'status': AmbulanceStatus.OS.name,
                            }), qos=0)

        # process messages
        self.loop(test_client, subscribe_client)

        # verify change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)

        # Modify hospital

        # retrieve current hospital status
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no comments')

        test_client.publish('user/{}/client/{}/hospital/{}/data'.format(self.u1.username,
                                                                        client_id,
                                                                        self.h1.id),
                            json.dumps({
                                'comment': 'no more comments',
                            }), qos=0)

        # process messages
        self.loop(test_client, subscribe_client)

        # verify change
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no more comments')

        # Modify hospital equipment

        # retrieve current equipment value
        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'True')

        test_client.publish('user/{}/client/{}/equipment/{}/item/{}/data'.format(self.u1.username,
                                                                                 client_id,
                                                                                 self.h1.equipmentholder.id,
                                                                                 self.e1.id),
                            json.dumps({
                                'value': 'False',
                            }), qos=0)

        # process messages
        self.loop(test_client, subscribe_client)

        # verify change
        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'False')

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()
        django_client.logout()


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
        broker['CLIENT_ID'] = 'test_websocket_mqtt_test_mqtt_publish'

        client = MQTTTestClient(broker,
                                transport='websockets',
                                tls_set={'ca_certs': None,
                                         'cert_reqs': ssl.CERT_NONE},
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_websocket_test_mqtt_subscribe'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # subscribe to ambulance/+/data
        topics = ('ambulance/{}/data'.format(self.a1.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'equipment/{}/item/{}/data'.format(self.h1.equipmentholder.id,
                                                     self.e1.id))

        # process messages
        self.loop(client)

        # expect more ambulance
        client.expect(topics[0])
        self.is_subscribed(client)

        # modify data in ambulance and save should trigger message
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)
        obj.status = AmbulanceStatus.OS.name
        obj.save()

        # process messages
        self.loop(client, subscribe_client)

        # assert change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)

        # expect more hospital and equipment
        [client.expect(t) for t in topics[1:]]

        # modify data in hospital and save should trigger message
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no comments')
        obj.comment = 'yet no comments'
        obj.save()

        # modify data in hospital_equipment and save should trigger message
        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'True')
        obj.value = 'False'
        obj.save()

        # process messages
        self.loop(client)
        client.wait()

        # assert changes
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet no comments')

        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'False')

        # Done?
        self.loop(client)
        client.wait()
