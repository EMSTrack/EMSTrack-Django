import json
import logging

from django.conf import settings
from django.test import Client as DjangoClient

from ambulance.models import AmbulanceStatus, CallStatus, CallPriority, Call, AmbulanceCallStatus, LocationType, \
    WaypointStatus
from ambulance.serializers import CallSerializer
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from .client import MQTTTestCase, MQTTTestClient, TestMQTT
from .client import MQTTTestSubscribeClient as SubscribeClient

logger = logging.getLogger(__name__)


# TODO: test that started_at, pending_at and ended_at get actually set in calls
# TODO: test that Call.abort() terminates a call properly in every stage of the call
# TODO: test call abort through api

class TestMQTTCallBase(TestMQTT):

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        self.subscribe_client = None

    def loop(self, *args, max_tries=10):
        super().loop(*args, self.subscribe_client, max_tries=max_tries)

    def wait(self, *clients):
        for client in clients:
            client.wait()
        self.subscribe_client.wait()

    def start_subscribe_client(self, client_id):

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start subscribe client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = client_id

        self.subscribe_client = SubscribeClient(broker, debug=True)
        self.is_connected(self.subscribe_client)
        self.is_subscribed(self.subscribe_client)

    def start_django_client(self, username, password):

        # start django client
        django_client = DjangoClient()

        # login as admin
        django_client.login(username=username, password=password)

        return django_client

    def set_django_client(self, django_client, client_id, ambulance_id, hospital_id, status=ClientStatus.O):

        # handshake ambulance and hospital
        response = django_client.post('/en/api/client/',
                                      content_type='application/json',
                                      data=json.dumps({
                                          'client_id': client_id,
                                          'status': status.name,
                                          'ambulance': ambulance_id
                                      }),
                                      follow=True)
        self.assertEqual(response.status_code, 201)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, status.name)
        self.assertEqual(clnt.ambulance.id, ambulance_id)
        self.assertEqual(clnt.hospital, hospital_id)

    def start_mqtt_client(self, client_id, username, password):

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start client

        broker.update(settings.MQTT)
        broker['USERNAME'] = username
        broker['PASSWORD'] = password
        broker['CLIENT_ID'] = client_id

        mqtt_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(mqtt_client)

        # Client handshake
        mqtt_client.publish('user/{}/client/{}/status'.format(username, client_id), ClientStatus.O.name)

        # process messages
        self.loop(mqtt_client)

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)

        return mqtt_client


class TestMQTTCalls(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id = 'test_mqtt_subscribe_admin'
        test_client = self.start_mqtt_client(client_id, username, password)

        # start django client
        django_client = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client, client_id, ambulance_id, None)

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
        self.loop(test_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # expect ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(ambulance_id))
        self.is_subscribed(test_client)

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id),
                            AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client)

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
        self.loop(test_client)

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client)

        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client)

        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, ambulance_id),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client)

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
        self.loop(test_client)

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
        self.loop(test_client)

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
        self.loop(test_client)

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

        # wait for disconnect
        self.wait(test_client)
        django_client.logout()


class TestMQTTCallsRegularUser(TestMQTTCalls):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


# -------------------------------------------------------------------------------------------
# New Testing 
# Test aborting the call once the call is created.
class TestMQTTCallsAbort(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id = 'test_mqtt_subscribe_admin'
        test_client = self.start_mqtt_client(client_id, username, password)

        # start django client
        django_client = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client, client_id, ambulance_id, None)

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

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # expect status ended call
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # Abort the call
        call.abort()

        # process messages
        self.loop(test_client)

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

        # wait for disconnect
        self.wait(test_client)
        django_client.logout()


class TestMQTTCallsDecline(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id = 'test_mqtt_subscribe_admin'
        test_client = self.start_mqtt_client(client_id, username, password)

        # start django client
        django_client = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client, client_id, ambulance_id, None)

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
        self.loop(test_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Declined" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), 
                            AmbulanceCallStatus.D.name)

        # process messages
        self.loop(test_client)

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
        self.loop(test_client)

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
        self.loop(test_client)

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

        # wait for disconnect
        self.wait(test_client)
        django_client.logout()


class TestMQTTCallsDeclineRegularUser(TestMQTTCallsDecline):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


class TestMQTTCallsDeclineInTheMiddle(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'], ambulance_id=None):

        if not ambulance_id:
            ambulance_id = self.a1.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id = 'test_mqtt_subscribe_admin'
        test_client = self.start_mqtt_client(client_id, username, password)

        # start django client
        django_client = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client, client_id, ambulance_id, None)

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
        self.loop(test_client)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Declined" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   ambulance_id, call.id), 
                            AmbulanceCallStatus.D.name)

        # process messages
        self.loop(test_client)

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
        self.loop(test_client)

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

        # wait for disconnect
        self.wait(test_client)
        django_client.logout()


class TestMQTTCallsDeclineInTheMiddleRegularUser(TestMQTTCallsDeclineInTheMiddle):

    def test(self):
        super().test('testuser2', 'very_secret', self.a3.id)


class TestMQTTCallsMultipleAmbulances(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'],
             ambulance_id1=None, ambulance_id2=None):

        if not ambulance_id1:
            ambulance_id1 = self.a1.id

        if not ambulance_id2:
            ambulance_id2 = self.a3.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id1 = 'test_mqtt1'
        test_client1 = self.start_mqtt_client(client_id1, username, password)

        # start django client
        django_client1 = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client1, client_id1, ambulance_id1, None)

        # subscribe to call and ambulance call status
        test_client1.expect('ambulance/{}/call/+/status'.format(ambulance_id1))
        self.is_subscribed(test_client1)

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
        self.loop(test_client1)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Accepted" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id1,
                                                                                    ambulance_id1, call.id),
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client1)

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
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "at patient" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "hospital bound" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "at hospital" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "completed" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id1,
                                                                                    ambulance_id1, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client1)

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
        test_client1.publish('user/{}/client/{}/status'.format(username, client_id1), ClientStatus.F.name)

        # process messages
        self.loop(test_client1)

        # wait for disconnect
        test_client1.wait()

        # Start second test client
        client_id2 = 'test_mqtt2'
        username2 = 'testuser2'
        password2 = 'very_secret'
        test_client2 = self.start_mqtt_client(client_id2, username2, password2)

        # start django client
        django_client2 = self.start_django_client(username2, password2)

        # login ambulance
        self.set_django_client(django_client2, client_id2, ambulance_id2, None)

        # Check if call status is Starting
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall1 status is Completed
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall2 status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client2)

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
        self.loop(test_client2)

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "at hospital" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "completed" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client2)

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
        self.loop(test_client2)

        # wait for disconnect
        self.wait(test_client2)
        django_client1.logout()
        django_client2.logout()


# TODO: Create another test where 2 clients to handle two ambulances simultaneously
class TestMQTTCallsMultipleAmbulancesSameTime(TestMQTTCallBase, MQTTTestCase):

    def test(self, username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'],
             ambulance_id1=None, ambulance_id2=None):

        if not ambulance_id1:
            ambulance_id1 = self.a1.id

        if not ambulance_id2:
            ambulance_id2 = self.a3.id

        # starts subscribe client
        self.start_subscribe_client('test_mqtt_subscribe_client')

        # Start test client
        client_id1 = 'test_mqtt1'
        test_client1 = self.start_mqtt_client(client_id1, username, password)

        # start django client
        django_client1 = self.start_django_client(username, password)

        # login ambulance
        self.set_django_client(django_client1, client_id1, ambulance_id1, None)

        # Start second test client
        client_id2 = 'test_mqtt2'
        username2 = 'testuser2'
        password2 = 'very_secret'
        test_client2 = self.start_mqtt_client(client_id2, username2, password2)

        # start django client
        django_client2 = self.start_django_client(username2, password2)

        # login ambulance
        self.set_django_client(django_client2, client_id2, ambulance_id2, None)

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
        self.loop(test_client1)

        # Check if call status is Pending
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.P.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Accepted" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id1,
                                                                                    ambulance_id1, call.id), 
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client1)

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to accepted
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id1)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.A.name)

        # Check if ambulancecall status is Requested
        ambulancecall = call.ambulancecall_set.get(ambulance_id=ambulance_id2)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes "Accepted" to call status
        test_client2.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username2, client_id2,
                                                                                    ambulance_id2, call.id),
                             AmbulanceCallStatus.A.name)

        # process messages
        self.loop(test_client2)

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
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client2 publishes "patient bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.PB.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "at patient" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "at patient" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.AP.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "hospital bound" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client1)

        # test_client publishes "hospital bound" to status
        test_client2.publish('user/{}/client/{}/ambulance/{}/data'.format(username2, client_id2, ambulance_id2),
                             json.dumps({
                                 'status': AmbulanceStatus.HB.name,
                             }))

        # process messages
        self.loop(test_client2)

        # test_client publishes "at hospital" to status
        test_client1.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id1, ambulance_id1),
                             json.dumps({
                                 'status': AmbulanceStatus.AH.name,
                             }))

        # process messages
        self.loop(test_client1)

        # subscribe to call
        test_client2.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client2)

        # will get call because of next call status change
        test_client1.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client1)

        # test_client publishes "completed" to call status
        test_client1.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id1,
                                                                                    ambulance_id1, call.id),
                             AmbulanceCallStatus.C.name)

        # process messages
        self.loop(test_client2, test_client1)

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
        self.loop(test_client2)

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
        self.loop(test_client2, test_client1)

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
        test_client1.publish('user/{}/client/{}/status'.format(username, client_id1), ClientStatus.F.name)

        # process messages
        self.loop(test_client1)

        # Client handshake
        test_client2.publish('user/{}/client/{}/status'.format(username2, client_id2), ClientStatus.F.name)

        # process messages
        self.loop(test_client2)

        # wait for disconnect
        self.wait(test_client1, test_client2)
        django_client1.logout()
        django_client2.logout()
