import ssl

from django.conf import settings

from ambulance.models import Ambulance, AmbulanceStatus
from hospital.models import Hospital, HospitalEquipment
from mqtt.tests.client import MQTTTestCase, MQTTTestClient, TestMQTT


class TestMQTTSubscribe(MQTTTestCase):

    def test(self):

        self.assertTrue(True)


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
                                tls_set={'ca_certs':'/etc/certificates/ca.crt',
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
