import json
import logging
import time

from django.conf import settings
from django.test import Client as DjangoClient
from django.utils import timezone

from ambulance.models import Ambulance, \
    AmbulanceStatus
from emstrack.tests.util import point2str
from equipment.models import EquipmentItem
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog
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
        topics = ('ambulance/{}/data'.format(self.a1.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'equipment/{}/item/{}/data'.format(self.h1.equipmentholder.id,
                                                     self.e1.id))
        self.is_subscribed(client)

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

        # Start client as testuser1
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topics = ('hospital/{}/data'.format(self.h1.id),
                  'equipment/{}/item/{}/data'.format(self.h1.equipmentholder.id,
                                                     self.e1.id))
        self.is_subscribed(client)

        # expect more hospital and equipment
        [client.expect(t) for t in topics]

        # modify data in hospital and save should trigger message
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet no comments')
        obj.comment = 'yet yet no comments'
        obj.save()

        # modify data in hospital_equipment and save should trigger message
        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'False')
        obj.value = 'True'
        obj.save()

        # process messages
        self.loop(client)
        client.wait()

        # assert changes
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet yet no comments')

        obj = EquipmentItem.objects.get(equipmentholder=self.h1.equipmentholder,
                                        equipment=self.e1)
        self.assertEqual(obj.value, 'True')

        # Start client as testuser2
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topics = ('ambulance/{}/data'.format(self.a3.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'equipment/{}/item/{}/data'.format(self.h1.equipmentholder.id,
                                                     self.e1.id))
        self.is_subscribed(client)

        # expect more ambulance
        client.expect(topics[0])

        # modify data in ambulance and save should trigger message
        obj = Ambulance.objects.get(id=self.a3.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)
        obj.status = AmbulanceStatus.OS.name
        obj.save()

        # process messages
        self.loop(client)

        # assert change
        obj = Ambulance.objects.get(id=self.a3.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)

        # expect more hospital and equipment
        [client.expect(t) for t in topics[1:]]

        # modify data in hospital and save should trigger message
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet yet no comments')
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


class TestMQTTWill(TestMQTT, MQTTTestCase):

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
        broker['CLIENT_ID'] = 'test_mqtt_will_admin'
        broker['WILL'] = {
            'topic': 'user/{}/client/{}/status'.format(broker['USERNAME'],
                                                       broker['CLIENT_ID']),
            'payload': ClientStatus.D.name
        }

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # Publish client status
        client.publish('user/{}/client/{}/status'.format(broker['USERNAME'],
                                                         broker['CLIENT_ID']),
                       ClientStatus.O.name,
                       qos=1,
                       retain=False)

        # process messages
        self.loop(client)

        # reconnecting with same client-id will trigger will
        client.expect('user/{}/client/{}/status'.format(broker['USERNAME'],
                                                        broker['CLIENT_ID']),
                      ClientStatus.D.name)
        self.is_subscribed(client)

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # process messages
        self.loop(client)

        # wait for disconnect
        client.wait()


class TestMQTTHandshakeDisconnect(TestMQTT, MQTTTestCase):

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
        broker['WILL'] = {
            'topic': 'user/{}/client/{}/status'.format(username, client_id),
            'payload': ClientStatus.D.name
        }

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Client handshake: force disconnected to trigger will
        test_client.client._sock.close()

        # process messages
        subscribe_client.loop()
        subscribe_client.loop()
        time.sleep(1)

        # process messages
        subscribe_client.loop()
        time.sleep(1)

        # process messages
        subscribe_client.loop()
        time.sleep(1)

        # wait for disconnect
        subscribe_client.wait()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.D.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.D.name)


class TestMQTTHandshakeReconnect(TestMQTT, MQTTTestCase):

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
        broker['WILL'] = {
            'topic': 'user/{}/client/{}/status'.format(username, client_id),
            'payload': ClientStatus.D.name
        }

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # reconnecting with same client-id, forces a disconnect
        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=False)
        self.is_connected(test_client)

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)

        # Client handshake: offline
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 4)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)
        self.assertEqual(obj[2].status, ClientStatus.D.name)
        self.assertEqual(obj[3].status, ClientStatus.F.name)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

