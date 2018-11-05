import json
import logging

from django.conf import settings
from django.utils import timezone

from ambulance.models import Ambulance, \
    AmbulanceStatus, CallStatus, CallPriority, Call, AmbulanceCallStatus
from ambulance.serializers import CallSerializer
from emstrack.tests.util import point2str
from hospital.models import Hospital, \
    HospitalEquipment
from login.models import Client, ClientStatus, ClientLog
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from ..subscribe import SubscribeClient

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
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

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
                            'ambulance login')

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
            'ambulancecall_set': [{'ambulance_id': ambulance_id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), "accepted")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Finished" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), "finished")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # expect blank call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # expect blank ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

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
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

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
                            'ambulance login')

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
            'ambulancecall_set': [{'ambulance_id': ambulance_id}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()
        
        # Abort the call
        call.abort()

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if call status is Ended
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # expect blank call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # expect blank ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()



















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
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

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
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id1),
                            'ambulance login')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [{'ambulance_id': ambulance_id1}, {'ambulance_id': ambulance_id2}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id), "accepted")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Finished" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id), "finished")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect 'Completed' ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), 'online')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client2.publish('user/{}/client/{}/ambulance/{}/status'.format(username2, client_id2, ambulance_id2),
                             'ambulance login')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id2)

        # subscribe ambulance call status
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

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
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             "accepted")

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # subscribe ambulance call status
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall2 status is Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # subscribe to call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "patient bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "at hospital" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "Finished" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                   ambulance_id2, call.id),
                             "finished")

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # expect blank ambulancecall
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # expect blank call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

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
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), 'offline')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

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

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

         # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

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
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, ambulance_id1),
                            'ambulance login')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id1)

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

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
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), 'online')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        # Ambulance handshake: ambulance login
        test_client2.publish('user/{}/client/{}/ambulance/{}/status'.format(username2, client_id2, ambulance_id2),
                             'ambulance login')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id2)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id2)

        # subscribe ambulance call status
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [{'ambulance_id': ambulance_id1}, {'ambulance_id': ambulance_id2}],
            'patient_set': [{'name': 'Jose', 'age': 3}, {'name': 'Maria', 'age': 10}]
        }
        serializer = CallSerializer(data=call)
        serializer.is_valid()
        call = serializer.save(updated_by=self.u1)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

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
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id), "accepted")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # test_client publishes client_id to location_client
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'location_client_id': client_id2,
                              }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             "accepted")

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # subscribe ambulance call status
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # Check if ambulancecall2 status is Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # subscribe to call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client2 publishes "patient bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id1),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Finished" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id1, call.id), "finished")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect 'Completed' ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if ambulancecall status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # test_client publishes "at hospital" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # test_client publishes "Finished" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                   ambulance_id2, call.id), "finished")

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # expect blank ambulancecall
        test_client2.expect('ambulance/{}/call/+/status'.format(ambulance_id2))
        self.is_subscribed(test_client2)

        # expect blank call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # expect blank ambulancecall
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client)

        # expect blank call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)
        self.loop(test_client2)
        subscribe_client.loop()

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
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), 'offline')

        # process messages
        self.loop(test_client2)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        test_client2.wait()
        subscribe_client.wait()

