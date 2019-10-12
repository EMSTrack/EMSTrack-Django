import logging
import time

from django.conf import settings

from login.models import Client, ClientStatus, ClientLog
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from .client import MQTTTestSubscribeClient as SubscribeClient

logger = logging.getLogger(__name__)


class TestMQTTWill(TestMQTT, MQTTTestCase):

    def test(self):

        # Start client as admin
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_will_1'
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
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_handshake_disconnet_1'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client

        broker.update(settings.MQTT)
        client_id = 'test_handshake_disconnet_2'
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
        obj = ClientLog.objects.filter(client=clnt)
        nrecords = len(obj) - 1
        obj = obj.last()
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
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')
        self.assertEqual(len(obj), nrecords + 2)
        self.assertEqual(obj[0].status, ClientStatus.D.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)


class TestMQTTHandshakeReconnect(TestMQTT, MQTTTestCase):

    def test(self):
        # Start client as admin
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_reconnect_1'

        subscribe_client = SubscribeClient(broker,
                                           debug=True)
        self.is_connected(subscribe_client)
        self.is_subscribed(subscribe_client)

        # Start test client

        broker.update(settings.MQTT)
        client_id = 'test_reconnect_2'
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
        obj = ClientLog.objects.filter(client=clnt)
        nrecords = len(obj) - 1
        obj = obj.last()
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
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')
        self.assertEqual(len(obj), nrecords + 2)
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
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')
        objs = [obj[0].status, obj[1].status, obj[2].status, obj[3].status]
        logger.debug(objs)
        self.assertCountEqual(
            objs,
            [ClientStatus.F.name, ClientStatus.O.name, ClientStatus.O.name, ClientStatus.D.name]
        )
        logger.debug(len(obj))
        logger.debug(nrecords)
        self.assertTrue(len(obj) - nrecords >= 3)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

