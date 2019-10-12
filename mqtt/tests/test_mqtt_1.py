from django.conf import settings

from ambulance.models import Ambulance, AmbulanceStatus
from equipment.models import EquipmentItem
from hospital.models import Hospital
from mqtt.tests.client import TestMQTT, MQTTTestCase, MQTTTestClient
from mqtt.tests.test_mqtt import logger


class TestMQTTPublish(TestMQTT, MQTTTestCase):

    def test_publish(self):
        # Start client as admin
        broker = {
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_publish_1'

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
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_publish_2'
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'

        logger.debug(broker)
        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=True)
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
            'HOST': settings.MQTT['BROKER_TEST_HOST'],
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }

        # Start test client

        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_publish_3'
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