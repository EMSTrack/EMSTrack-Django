import json
import ssl

from django.conf import settings

from ambulance.models import Ambulance, AmbulanceStatus
from hospital.models import Hospital, HospitalEquipment
from login.models import Client, ClientStatus, ClientLog
from mqtt.subscribe import SubscribeClient
from mqtt.tests.client import MQTTTestCase, MQTTTestClient, TestMQTT


class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test(self):

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 8884,
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
                                     transport='websockets',
                                     tls_set={'ca_certs': None,
                                              'cert_reqs': ssl.CERT_NONE},
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

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()


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
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'

        client = MQTTTestClient(broker,
                                transport='websockets',
                                tls_set={'ca_certs': None,
                                         'cert_reqs': ssl.CERT_NONE},
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topics = ('ambulance/{}/data'.format(self.a1.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                         self.e1.id))
        [client.expect(t) for t in topics]
        self.is_subscribed(client)

        # process messages
        self.loop(client)

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
        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'True')
        obj.value = 'False'
        obj.save()

        # process messages
        self.loop(client)
        client.wait()

        # assert changes
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet no comments')

        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'False')

        # Done?
        self.loop(client)
        client.wait()
