import json
import logging

from django.conf import settings

from ambulance.models import AmbulanceStatus, CallStatus, CallPriority, Call, AmbulanceCallStatus, LocationType, \
    WaypointStatus
from ambulance.serializers import CallSerializer
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from .client import MQTTTestSubscribeClient as SubscribeClient

logger = logging.getLogger(__name__)


# TODO: test that started_at, pending_at and ended_at get actually set in calls
# TODO: test that Call.abort() terminates a call properly in every stage of the call

class TestMQTTCalls(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id),
                            ClientActivity.AI.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [
                {
                    'ambulance_id': ambulance_id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                }
                ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # expect ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id),
                            AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # test_client publishes new waypoint
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/waypoint/{}/data'.format(username, client_id,
                                                                                             ambulance_id, call.id, -1),
                            json.dumps({
                                'order': 2,
                                'location': {
                                    'type': LocationType.w.name
                                }
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # has the waypoint been created?
        waypoint_set = ambulancecall.waypoint_set.all()
        self.assertEqual(len(waypoint_set), 2)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client updates waypoint
        waypoint = waypoint_set.get(order=2)
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/waypoint/{}/data'.format(username, client_id,
                                                                                             ambulance_id, call.id,
                                                                                             waypoint.id),
                            json.dumps({
                                'order': 1,
                                'status': WaypointStatus.V.name
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # has the waypoint been created?
        waypoint = ambulancecall.waypoint_set.all()
        self.assertEqual(len(waypoint), 2)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client publishes "completed" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id),
                            AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()


class TestMQTTCallsRegularUser(TestMQTTCalls):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


# -------------------------------------------------------------------------------------------
# New Testing 
# Test aborting the call once the call is created.
class TestMQTTCallsAbort(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
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

        # Ambulance handshake: ambulance login
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id),
                            ClientActivity.AI.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [{'ambulance_id': ambulance_id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # expect status ended call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # Abort the call
        call.abort()

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()


class TestMQTTCallsDecline(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id),
                            ClientActivity.AI.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [
                {
                    'ambulance_id': ambulance_id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                }
                ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "Declined" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), 
                            AmbulanceCallStatus.D.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Declined
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.D.name)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), 
                            AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # expect status ended call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # expect status completed ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client publishes "completed" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id),
                            AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()


class TestMQTTCallsDeclineRegularUser(TestMQTTCallsDecline):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


class TestMQTTCallsDeclineInTheMiddle(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
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

        # Ambulance handshake: ambulance login
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id),
                            ClientActivity.AI.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [
                {
                    'ambulance_id': ambulance_id,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                }
                ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "Declined" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), 
                            AmbulanceCallStatus.D.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Declined
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.D.name)

        # expect status ended call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # Abort call
        call.abort()

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()


class TestMQTTCallsDeclineInTheMiddleRegularUser(TestMQTTCallsDeclineInTheMiddle):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


class TestMQTTCallsMultipleAmbulances(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'],
             ambulance_id1=None, ambulance_id2=None):

        if not ambulance_id1:
            ambulance_id1 = self.a1.id

        if not ambulance_id2:
            ambulance_id2 = self.a3.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client = MQTTTestClient(broker,
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

        # Ambulance handshake: ambulance login
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id1),
                            ClientActivity.AI.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id1)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [
                {
                    'ambulance_id': ambulance_id1,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': ambulance_id2,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                }
                ],
            # 'ambulancecall_set': [{'ambulance_id': ambulance_id1}, {'ambulance_id': ambulance_id2}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id), 
                            AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client, subscribe_client)

        # test_client publishes "completed" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id),
                            AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client, subscribe_client)

        # wait for disconnect
        test_client.wait()

        # Start second test client

        username2 = 'testuser2'
        password2 = 'very_secret'
        client_id2 = 'test_mqtt_subscribe2'

        broker.update(settings.MQTT)
        broker['USERNAME'] = username2
        broker['PASSWORD'] = password2
        broker['CLIENT_ID'] = client_id2

        test_client2 = MQTTTestClient(broker,
                                      check_payload=False,
                                      debug=True)
        self.is_connected(test_client2)

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), ClientStatus.O.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client2.publish('user/{}/client/{}/ambulance/{}/status'.format(username2, client_id2, ambulance_id2),
                             ClientActivity.AI.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id2)

        # Check if call status is Starting
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall2 status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'location_client_id': client_id2,
                              }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall2 status is accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # test_client publishes "patient bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "at hospital" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "completed" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # Check if ambulancecall1 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall2 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), ClientStatus.F.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # wait for disconnect
        test_client2.wait()
        subscribe_client.wait()


# TODO: Create another test where 2 clients to handle two ambulances simultaneously
class TestMQTTCallsMultipleAmbulancesSameTime(TestMQTT, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'],
             ambulance_id1=None, ambulance_id2=None):

        if not ambulance_id1:
            ambulance_id1 = self.a1.id

        if not ambulance_id2:
            ambulance_id2 = self.a3.id

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
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        test_client1 = MQTTTestClient(broker,
                                      check_payload=False,
                                      debug=True)
        self.is_connected(test_client1)

        # Client handshake
        test_client1.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(test_client1, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client1.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id1),
                             ClientActivity.AI.name)

        # process messages
        self.loop(test_client1, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id1)

        # Start second test client
        username2 = 'testuser2'
        password2 = 'very_secret'
        client_id2 = 'test_mqtt_subscribe2'

        broker.update(settings.MQTT)
        broker['USERNAME'] = username2
        broker['PASSWORD'] = password2
        broker['CLIENT_ID'] = client_id2

        test_client2 = MQTTTestClient(broker,
                                      check_payload=False,
                                      debug=True)
        self.is_connected(test_client2)

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), ClientStatus.O.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client2.publish('user/{}/client/{}/ambulance/{}/status'.format(username2, client_id2, ambulance_id2),
                             ClientActivity.AI.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id2)

        # subscribe to call and ambulance call status
        test_client1.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client1)

        # subscribe ambulance call status
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # create call using serializer, two ambulances
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'ambulancecall_set': [
                {
                    'ambulance_id': ambulance_id1,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                },
                {
                    'ambulance_id': ambulance_id2,
                    'waypoint_set': [
                        {
                            'order': 0,
                            'location': {
                                'type': LocationType.i.name,
                                'number': '123',
                                'street': 'asdasdasd asd asd asdas'
                            }
                        }
                    ]
                }
                ],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client1, subscribe_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                             json.dumps({
                                 'location_client_id': client_id,
                             }))

        # process messages
        self.loop(test_client1, subscribe_client)

        # test_client publishes "Accepted" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                    ambulance_id1, call.id), 
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client1, subscribe_client)

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'location_client_id': client_id2,
                              }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # Check if ambulancecall2 status is accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # test_client publishes "patient bound" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client1, subscribe_client)

        # test_client2 publishes "patient bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "at patient" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client1, subscribe_client)

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "hospital bound" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client1, subscribe_client)

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # test_client publishes "at hospital" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client1, subscribe_client)

        # subscribe to call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # will get call because of next call status change
        test_client1.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client1)

        # test_client publishes "completed" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                    ambulance_id1, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client2, test_client1, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # test_client publishes "at hospital" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client2, subscribe_client)

        # subscribe to call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # will get call because of next call status change
        test_client1.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client1)

        # test_client publishes "completed" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client2, test_client1, subscribe_client)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Client handshake
        test_client1.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.F.name)

        # process messages
        self.loop(test_client1, subscribe_client)

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), ClientStatus.F.name)

        # process messages
        self.loop(test_client2, subscribe_client)

        # wait for disconnect
        test_client1.wait()
        test_client2.wait()
        subscribe_client.wait()
