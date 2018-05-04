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


class TestMQTTCalls(TestMQTT, MQTTTestCase):

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
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, self.a1.id),
                            'ambulance login')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, self.a1.id)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

    def _test(self):

        # subscribe to call and ambulance call status
        test_client.expect('ambulance/{}/call/+/status'.format(self.a1.id))
        self.is_subscribed(test_client)

        # create call using serializer, one ambulance first
        call = {
            'status': CallStatus.P.name,
            'priority': CallPriority.B.name,
            'number': '123',
            'street': 'asdasdasd asd asd asdas',
            'ambulancecall_set': [{'ambulance_id': self.a1.id}],
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
        ambulancecall = call.ambulancecall_set.get(ambulance_id=self.a1.id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # test_client publishes client_id to location_client
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, self.a1.id),
                            json.dumps({
                                'location_client_id': client_id,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "Accepted" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   self.a1.id, call.id), "Accepted")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status changed to Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status changed to Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=self.a1.id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.O.name)

        # subscribe to call and ambulance call status
        test_client.expect('call/{}/data'.format(call.id))
        self.is_subscribed(test_client)

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')



        # test_client publishes "patient bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, self.a1.id),
                            json.dumps({
                                'status': AmbulanceStatus.PB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # test_client publishes "at patient" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, self.a1.id),
                            json.dumps({
                                'status': AmbulanceStatus.AP.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()
        
        # test_client publishes "hospital bound" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, self.a1.id),
                            json.dumps({
                                'status': AmbulanceStatus.HB.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()
        
        # test_client publishes "at hospital" to status
        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(username, client_id, self.a1.id),
                            json.dumps({
                                'status': AmbulanceStatus.AH.name,
                            }))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()
        
        # test_client publishes "Finished" to call status
        test_client.publish('user/{}/client/{}/ambulance/{}/call/{}/status'.format(username, client_id,
                                                                                   self.a1.id, call.id), "Finished")

        # process messages
        self.loop(test_client)
        subscribe_client.loop()


        # Check if call status is Started
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.S.name)

        # Check if ambulancecall status is Ongoing
        ambulancecall = call.ambulancecall_set.get(ambulance_id=self.a1.id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.R.name)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Check if call status changed to Finished
        call = Call.objects.get(id=call.id)
        self.assertEqual(call.status, CallStatus.E.name)

        # Check if ambulancecall a1 status changed to Completed
        ambulancecall =  call.ambulancecall_set.get(ambulance_id=self.a1.id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)

        # Check if ambulancecall a2 status changed to Completed
        ambulancecall =  call.ambulancecall_set.get(ambulance_id=self.a2.id)
        self.assertEqual(ambulancecall.status, AmbulanceCallStatus.C.name)



    def _test(self):

        # Modify ambulance

        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        # retrieve message that is there already due to creation
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
        self.loop(test_client)
        subscribe_client.loop()

        # expect update once
        test_client.expect('ambulance/{}/data'.format(self.a1.id))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # verify change
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)

        # Modify hospital

        # retrieve current hospital status
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no comments')

        # retrieve message that is there already due to creation
        test_client.expect('hospital/{}/data'.format(self.h1.id))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/client/{}/hospital/{}/data'.format(self.u1.username, 
                                                                        client_id,
                                                                        self.h1.id),
                            json.dumps({
                                'comment': 'no more comments',
                            }), qos=0)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect update once
        test_client.expect('hospital/{}/data'.format(self.h1.id))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # verify change
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no more comments')

        # Modify hospital equipment

        # retrieve current equipment value
        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'True')

        # retrieve message that is there already due to creation
        test_client.expect('hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                                  self.e1.id))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/client/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                                     client_id,
                                                                                     self.h1.id,
                                                                                     self.e1.id),
                            json.dumps({
                                'value': 'False',
                            }), qos=0)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect update once
        test_client.expect('hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                                  self.e1.id))
        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # verify change
        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'False')

        # test bulk ambulance update

        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a2.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        # retrieve message that is there already due to creation
        test_client.expect('ambulance/{}/data'.format(self.a2.id))
        self.is_subscribed(test_client)

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

        test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username, 
                                                                         client_id,
                                                                         self.a2.id),
                            json.dumps(data), qos=0)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect update once
        test_client.expect('ambulance/{}/data'.format(self.a2.id))

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # verify change
        obj = Ambulance.objects.get(id=self.a2.id)
        self.assertEqual(obj.status, AmbulanceStatus.PB.name)
        self.assertEqual(obj.timestamp, timestamp)
        self.assertEqual(point2str(obj.location), point2str(location))

        # Client handshake
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.F.name)

        test_invalid_serializer = False
        if test_invalid_serializer:

            # generate ERROR: JSON formated incorrectly

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))
            self.is_subscribed(test_client)

            test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username,
                                                                             client_id,
                                                                             self.a1.id),
                                '{ "value": ',
                                qos=0)

            # process messages
            self.loop(test_client)
            subscribe_client.loop()

            # generate ERROR: JSON formated incorrectly

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))
            self.is_subscribed(test_client)

            test_client.publish('user/{}/client/{}/hospital/{}/data'.format(self.u1.username,
                                                                            client_id,
                                                                            self.h1.id),
                                '{ "value": ',
                                qos=0)

            # process messages
            self.loop(test_client)
            subscribe_client.loop()

            # generate ERROR: JSON formated incorrectly

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))
            self.is_subscribed(test_client)

            test_client.publish('user/{}/client/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                                         client_id,
                                                                                         self.h1.id,
                                                                                         self.e1.id),
                                '{ "value": ',
                                qos=0)

            # process messages
            self.loop(test_client)
            subscribe_client.loop()

            # WARNING: The next tests prevent the test database from
            # being removed at the end of the test. It is not clear why
            # but it could be django bug related to the LiveServerThread
            # not being thread safe:
            #
            # https://code.djangoproject.com/ticket/22420 Just run a
            #
            # limited set of tests that do not make use of
            # LiveServerThread for deleting the test database, for
            # example:
            #
            #     ./manage test ambulance.test

            # generate ERROR: wrong id

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))

            test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username, 
                                                                             client_id,
                                                                             1111),
                                json.dumps({
                                    'status': AmbulanceStatus.OS.name,
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: wrong id

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))

            test_client.publish('user/{}/client/{}/hospital/{}/data'.format(self.u1.username,
                                                                            client_id,
                                                                            1111),
                                json.dumps({
                                    'comment': 'comment',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: wrong id

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))

            test_client.publish('user/{}/client/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                                         client_id,
                                                                                         self.h1.id,
                                                                                         -1),
                                json.dumps({
                                    'comment': 'comment',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: invalid serializer

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))

            test_client.publish('user/{}/client/{}/ambulance/{}/data'.format(self.u1.username, 
                                                                             client_id,
                                                                             self.a1.id),
                                json.dumps({
                                    'status': 'Invalid',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()
            self.loop(test_client)
            subscribe_client.loop()

            # generate ERROR: invalid serializer

            test_client.expect('user/{}/client/{}/error'.format(broker['USERNAME'], client_id))

            test_client.publish('user/{}/client/{}/hospital/{}/data'.format(self.u1.username,
                                                                            client_id,
                                                                            self.h1.id),
                                json.dumps({
                                    'location': 'PPOINT()',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()
            self.loop(test_client)
            subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

