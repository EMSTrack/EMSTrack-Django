import json

from django.conf import settings
from django.test import Client as DjangoClient
from django.utils import timezone

from ambulance.models import Ambulance, AmbulanceStatus
from emstrack.tests.util import point2str
from equipment.models import EquipmentItem
from hospital.models import Hospital
from login.models import ClientStatus, Client
from mqtt.tests.client import TestMQTT, MQTTTestCase, MQTTTestSubscribeClient as SubscribeClient, MQTTTestClient


class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test_subscribe(self):

        # Start client as admin
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_subscribe_1'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client
        broker.update(settings.MQTT)
        client_id = 'test_subscribe_2'
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

        # Modify ambulance

        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        # expect update once
        test_client.expect('ambulance/{}/data'.format(self.a1.id))
        self.is_subscribed(test_client)

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

        # expect update once
        test_client.expect('hospital/{}/data'.format(self.h1.id))
        self.is_subscribed(test_client)

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

        # expect update once
        test_client.expect('equipment/{}/item/{}/data'.format(self.h1.equipmentholder.id,
                                                              self.e1.id))
        self.is_subscribed(test_client)

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

        # test bulk ambulance update

        # expect null client after logout
        test_client.expect('ambulance/{}/data'.format(self.a1.id))
        self.is_subscribed(test_client)

        # handshake ambulance
        response = django_client.post('/en/api/client/',
                                      content_type='application/json',
                                      data=json.dumps({
                                          'client_id': client_id,
                                          'status': ClientStatus.O.name,
                                          'ambulance': self.a2.id,
                                      }),
                                      follow=True)
        # result = JSONParser().parse(BytesIO(response.content))
        # logger.debug(result)
        self.assertEqual(response.status_code, 201)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, self.a2)
        self.assertEqual(clnt.hospital, self.h1)

        # retrieve last ambulance
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(hasattr(obj, 'client'), False)

        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a2.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        location = {'latitude': -2., 'longitude': 7.}
        timestamp = timezone.now()
        data = [
            {
                'status': AmbulanceStatus.OS.name,
            },
            {
                'status': AmbulanceStatus.AV.name,
                'location': location,
            },
            {
                'status': AmbulanceStatus.PB.name,
                'timestamp': str(timestamp)
            }
        ]

        # expect update once
        test_client.expect('ambulance/{}/data'.format(self.a2.id))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username,
                                                                         client_id,
                                                                         self.a2.id),
                            json.dumps(data), qos=0)

        # process messages
        self.loop(test_client, subscribe_client)

        # verify change
        obj = Ambulance.objects.get(id=self.a2.id)
        self.assertEqual(obj.status, AmbulanceStatus.PB.name)
        self.assertEqual(obj.timestamp, timestamp)
        self.assertEqual(point2str(obj.location), point2str(location))

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