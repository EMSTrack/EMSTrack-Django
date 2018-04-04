import logging
import time

from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone

from rest_framework.renderers import JSONRenderer
import json

from emstrack.tests.util import point2str
from login.models import UserProfile, Client, ClientStatus, ClientLog, ClientActivity
from login.permissions import get_permissions

from login.serializers import UserProfileSerializer
from login.views import SettingsView

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability
from ambulance.serializers import AmbulanceSerializer

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType
from hospital.serializers import EquipmentSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer

from .client import MQTTTestCase, MQTTTestClient

from ..subscribe import SubscribeClient

logger = logging.getLogger(__name__)


class TestMQTT:

    def is_connected(self, client, MAX_TRIES=10):

        # connected?
        k = 0
        while not client.connected and k < MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)

    def is_subscribed(self, client, MAX_TRIES=10):

        client.loop_start()

        # connected?
        k = 0
        while len(client.subscribed) and k < MAX_TRIES:
            k += 1
            time.sleep(1)

        client.loop_stop()

        self.assertEqual(len(client.subscribed), 0)

    def loop(self, *clients, MAX_TRIES=10):

        # logger.debug('clients = {}'.format(clients))
        # logger.debug('MAX_TRIES = {}'.format(MAX_TRIES))

        # starts clients
        for client in clients:
            client.loop_start()

        # connected?
        k = 0
        done = False
        while not done and k < MAX_TRIES:
            done = True
            for client in clients:
                done = done and client.done()
            k += 1
            time.sleep(1)

        # stop clients
        for client in clients:
            client.loop_stop()

        if not done:
            # logging.debug('NOT DONE:')
            for client in clients:
                if hasattr(client, 'expecting') and hasattr(client, 'publishing'):
                    logging.debug(('expecting = {}, ' +
                                   'publishing = {}').format(client.expecting,
                                                             client.publishing))

        self.assertEqual(done, True)


class TestMQTTSeed(TestMQTT, MQTTTestCase):

    def test_mqttseed(self):

        # seed
        from django.core import management

        management.call_command('mqttseed',
                                verbosity=1)

        print('>> Processing messages...')

        # Start client as admin
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqttseed_admin'

        client = MQTTTestClient(broker)
        self.is_connected(client)

        qos = 0

        # Expect settings
        client.expect('settings',
                      JSONRenderer().render(SettingsView.get_settings()),
                      qos)

        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for user in User.objects.all():
            client.expect('user/{}/profile'.format(user.username),
                          JSONRenderer().render(UserProfileSerializer(user).data),
                          qos)

        # Subscribed?
        self.is_subscribed(client)

        # Done?
        self.loop(client)
        client.wait()

        # Repeat with same client

        client = MQTTTestClient(broker)
        self.is_connected(client)

        qos = 0

        # Expect settings
        client.expect('settings',
                      JSONRenderer().render(SettingsView.get_settings()),
                      qos)

        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for user in User.objects.all():
            client.expect('user/{}/profile'.format(user.username),
                          JSONRenderer().render(UserProfileSerializer(user).data),
                          qos)

        # Subscribed?
        self.is_subscribed(client)

        # Done?
        self.loop(client)
        client.wait()

        # Repeat with same client and different qos

        client = MQTTTestClient(broker)
        self.is_connected(client)

        qos = 2

        # Expect settings
        client.expect('settings',
                      JSONRenderer().render(SettingsView.get_settings()),
                      qos)

        # Expect all ambulances
        for ambulance in Ambulance.objects.all():
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # Expect all hospitals
        for hospital in Hospital.objects.all():
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            hospital_equipment = hospital.hospitalequipment_set.values('equipment')
            equipment = Equipment.objects.filter(id__in=hospital_equipment)
            client.expect('hospital/{}/metadata'.format(hospital.id),
                          JSONRenderer().render(EquipmentSerializer(equipment, many=True).data),
                          qos)

        # Expect all hospital equipments
        for e in HospitalEquipment.objects.all():
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Expect all profiles
        for user in User.objects.all():
            client.expect('user/{}/profile'.format(user.username),
                          JSONRenderer().render(UserProfileSerializer(user).data),
                          qos)

        # Subscribed?
        self.is_subscribed(client)

        # Done?
        self.loop(client)
        client.wait()

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1'

        client = MQTTTestClient(broker)
        self.is_connected(client)

        # Expect settings
        client.expect('settings',
                      JSONRenderer().render(SettingsView.get_settings()),
                      qos)

        # Expect user profile
        user = User.objects.get(username='testuser1')
        client.expect('user/testuser1/profile',
                      JSONRenderer().render(UserProfileSerializer(user).data),
                      qos)

        # User Ambulances
        can_read = get_permissions(user).get_can_read('ambulances')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # User Hospitals
        can_read = get_permissions(user).get_can_read('hospitals')
        for hospital in Hospital.objects.filter(id__in=can_read):
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)

        # Expect all user hospital equipments
        for e in HospitalEquipment.objects.filter(hospital__id__in=can_read):
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Subscribed?
        self.is_subscribed(client)

        # Done?
        self.loop(client)
        client.wait()

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser2'

        client = MQTTTestClient(broker)
        self.is_connected(client)

        # Expect settings
        client.expect('settings',
                      JSONRenderer().render(SettingsView.get_settings()),
                      qos)

        # Expect user profile
        user = User.objects.get(username='testuser2')
        client.expect('user/testuser2/profile',
                      JSONRenderer().render(UserProfileSerializer(user).data),
                      qos)

        # User Ambulances
        can_read = get_permissions(user).get_can_read('ambulances')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)

        # User Hospitals
        can_read = get_permissions(user).get_can_read('hospitals')
        for hospital in Hospital.objects.filter(id__in=can_read):
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)

        # Expect all user hospital equipments
        for e in HospitalEquipment.objects.filter(hospital__id__in=can_read):
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Subscribed?
        self.is_subscribed(client)

        # Done?
        self.loop(client)
        client.wait()


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
                                debug=False)
        self.is_connected(client)

        # subscribe to ambulance/+/data
        topics = ('ambulance/{}/data'.format(self.a1.id),
                  'hospital/{}/data'.format(self.h1.id),
                  'hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                         self.e1.name))
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
                  'hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                         self.e1.name))
        [client.expect(t) for t in topics]
        self.is_subscribed(client)

        # process messages
        self.loop(client)

        # expect more hospital and equipment
        [client.expect(t) for t in topics]

        # modify data in hospital and save should trigger message
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet no comments')
        obj.comment = 'yet yet no comments'
        obj.save()

        # modify data in hospital_equipment and save should trigger message
        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'False')
        obj.value = 'True'
        obj.save()

        # process messages
        self.loop(client)
        client.wait()

        # assert changes
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet yet no comments')

        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
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
                  'hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                         self.e1.name))
        [client.expect(t) for t in topics]
        self.is_subscribed(client)

        # process messages
        self.loop(client)

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
        test_client.publish('user/{}/ambulance/{}/data'.format(self.u1.username,
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

        test_client.publish('user/{}/hospital/{}/data'.format(self.u1.username,
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
                                                                  self.e1.name))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                           self.h1.id,
                                                                           self.e1.name),
                            json.dumps({
                                'value': 'False',
                            }), qos=0)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # expect update once
        test_client.expect('hospital/{}/equipment/{}/data'.format(self.h1.id,
                                                                  self.e1.name))
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

        test_client.publish('user/{}/ambulance/{}/data'.format(self.u1.username,
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

        # generate ERROR: JSON formated incorrectly

        test_client.expect('user/{}/error'.format(broker['USERNAME']))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/ambulance/{}/data'.format(self.u1.username,
                                                               self.a1.id),
                            '{ "value": ',
                            qos=0)

        # process messages
        self.loop(test_client, subscribe_client)
        subscribe_client.loop()

        # generate ERROR: JSON formated incorrectly

        test_client.expect('user/{}/error'.format(broker['USERNAME']))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/hospital/{}/data'.format(self.u1.username,
                                                              self.h1.id),
                            '{ "value": ',
                            qos=0)

        # process messages
        self.loop(test_client, subscribe_client)
        subscribe_client.loop()

        # generate ERROR: JSON formated incorrectly

        test_client.expect('user/{}/error'.format(broker['USERNAME']))
        self.is_subscribed(test_client)

        test_client.publish('user/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                           self.h1.id,
                                                                           self.e1.name),
                            '{ "value": ',
                            qos=0)

        # process messages
        self.loop(test_client, subscribe_client)
        subscribe_client.loop()

        test_invalid_serializer = False
        if test_invalid_serializer:
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

            test_client.expect('user/{}/error'.format(broker['USERNAME']))

            test_client.publish('user/{}/ambulance/{}/data'.format(self.u1.username,
                                                                   1111),
                                json.dumps({
                                    'status': AmbulanceStatus.OS.name,
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: wrong id

            test_client.expect('user/{}/error'.format(broker['USERNAME']))

            test_client.publish('user/{}/hospital/{}/data'.format(self.u1.username,
                                                                  1111),
                                json.dumps({
                                    'comment': 'comment',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: wrong id

            test_client.expect('user/{}/error'.format(broker['USERNAME']))

            test_client.publish('user/{}/hospital/{}/equipment/{}/data'.format(self.u1.username,
                                                                               self.h1.id,
                                                                               'unknown'),
                                json.dumps({
                                    'comment': 'comment',
                                }), qos=0)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # generate ERROR: invalid serializer

            test_client.expect('user/{}/error'.format(broker['USERNAME']))

            test_client.publish('user/{}/ambulance/{}/data'.format(self.u1.username,
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

            test_client.expect('user/{}/error'.format(broker['USERNAME']))

            test_client.publish('user/{}/hospital/{}/data'.format(self.u1.username,
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
            'payload': 'disconnected'
        }

        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        # Expect status
        client.expect('user/{}/client/{}/status'.format(broker['USERNAME'],
                                                        broker['CLIENT_ID']),
                      'online')
        self.is_subscribed(client)

        # Publish client status
        client.publish('user/{}/client/{}/status'.format(broker['USERNAME'],
                                                         broker['CLIENT_ID']),
                       'online',
                       qos=1,
                       retain=True)

        # process messages
        self.loop(client)

        # reconnecting with same client-id will trigger will
        client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(client)

        client.expect('user/{}/client/{}/status'.format(broker['USERNAME'],
                                                        broker['CLIENT_ID']),
                      'disconnected')
        self.is_subscribed(client)

        # process messages
        self.loop(client)

        # wait for disconnect
        client.wait()


class TestMQTTHandshake(TestMQTT, MQTTTestCase):

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
        subscribe_client_id = 'test_mqttclient'
        broker['CLIENT_ID'] = subscribe_client_id

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

        # Start second test client

        broker.update(settings.MQTT)
        second_client_id = 'test_mqtt_subscribe_admin_second'
        username = broker['USERNAME']
        broker['CLIENT_ID'] = second_client_id

        second_test_client = MQTTTestClient(broker,
                                            check_payload=False,
                                            debug=True)
        self.is_connected(second_test_client)

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, None)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.HS.name)

        # Client handshake: online
        second_test_client.publish('user/{}/client/{}/status'.format(username, second_client_id), 'online')

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=second_client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, None)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.HS.name)

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

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.AI.name)
        self.assertEqual(obj.details, self.a1.identifier)

        # Ambulance handshake: ambulance login
        second_test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, second_client_id, self.a2.id),
                                   'ambulance login')

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=second_client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance.id, self.a2.id)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.AI.name)
        self.assertEqual(obj.details, self.a2.identifier)

        # check record
        ambulance = Ambulance.objects.get(id=self.a2.id)
        self.assertEqual(ambulance.location_client, None)

        # Start streaming data
        test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a1.id),
                            '{"location_client_id":"' + client_id + '"}', qos=2)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record log
        obj = ClientLog.objects.filter(client=Client.objects.get(client_id=client_id)).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.SL.name)
        self.assertEqual(obj.details, self.a1.identifier)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertFalse(ambulance.location_client is None)
        self.assertEqual(ambulance.location_client.client_id, client_id)

        # Try to change location client without reset to a valid client_id
        second_test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a1.id),
                                   '{"location_client_id":"' + second_client_id + '"}', qos=2)

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertFalse(ambulance.location_client is None)
        self.assertEqual(ambulance.location_client.client_id, client_id)

        # reset location_client
        test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a1.id),
                            '{"location_client_id":""}', qos=2)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record log
        obj = ClientLog.objects.filter(client=Client.objects.get(client_id=client_id)).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.TL.name)
        self.assertEqual(obj.details, self.a1.identifier)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertTrue(ambulance.location_client is None)

        #############################################################################################

        if False:

            # Try to change location client without reset to an invalid client_id
            test_client.expect('user/{}/error'.format(username))
            self.is_subscribed(test_client)

            test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a1.id),
                                '{"location_client_id":"' + client_id + '_other"}', qos=2)

            # process messages
            self.loop(test_client, subscribe_client)
            subscribe_client.loop()

            # process messages
            self.loop(test_client)
            subscribe_client.loop()

            # check record
            ambulance = Ambulance.objects.get(id=self.a1.id)
            self.assertFalse(ambulance.location_client is None)
            self.assertEqual(ambulance.location_client.client_id, client_id)

        #############################################################################################

        # Second client start streaming data
        second_test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a2.id),
                                   '{"location_client_id":"' + second_client_id + '"}', qos=2)

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # check record
        ambulance = Ambulance.objects.get(id=self.a2.id)
        self.assertFalse(ambulance.location_client is None)
        self.assertEqual(ambulance.location_client.client_id, second_client_id)

        # Ambulance handshake: ambulance logout
        test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, client_id, self.a1.id),
                            'ambulance logout')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, None)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.AO.name)
        self.assertEqual(obj.details, self.a1.identifier)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a2.id)
        self.assertFalse(ambulance.location_client is None)
        self.assertEqual(ambulance.location_client.client_id, second_client_id)

        # Ambulance handshake: ambulance logout
        second_test_client.publish('user/{}/client/{}/ambulance/{}/status'.format(username, second_client_id, self.a2.id),
                                   'ambulance logout')

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # check client record
        clnt = Client.objects.get(client_id=second_client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, None)

        # check client record log
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.AO.name)
        self.assertEqual(obj.details, self.a2.identifier)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a2.id)
        self.assertTrue(ambulance.location_client is None)

        # Client handshake: offline
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # Client handshake: offline
        second_test_client.publish('user/{}/client/{}/status'.format(username, second_client_id), 'offline')

        # process messages
        self.loop(second_test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        second_test_client.wait()
        subscribe_client.wait()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 6)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[0].activity, ClientActivity.HS.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)
        self.assertEqual(obj[1].activity, ClientActivity.AI.name)
        self.assertEqual(obj[1].details, self.a1.identifier)
        self.assertEqual(obj[2].status, ClientStatus.O.name)
        self.assertEqual(obj[2].activity, ClientActivity.SL.name)
        self.assertEqual(obj[2].details, self.a1.identifier)
        self.assertEqual(obj[3].status, ClientStatus.O.name)
        self.assertEqual(obj[3].activity, ClientActivity.TL.name)
        self.assertEqual(obj[3].details, self.a1.identifier)
        self.assertEqual(obj[4].activity, ClientActivity.AO.name)
        self.assertEqual(obj[4].details, self.a1.identifier)
        self.assertEqual(obj[5].status, ClientStatus.F.name)
        self.assertEqual(obj[5].activity, ClientActivity.HS.name)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertFalse(ambulance.location_client is True)

        # check record
        clnt = Client.objects.get(client_id=second_client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 6)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[0].activity, ClientActivity.HS.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)
        self.assertEqual(obj[1].activity, ClientActivity.AI.name)
        self.assertEqual(obj[1].details, self.a2.identifier)
        self.assertEqual(obj[2].status, ClientStatus.O.name)
        self.assertEqual(obj[2].activity, ClientActivity.SL.name)
        self.assertEqual(obj[2].details, self.a2.identifier)
        self.assertEqual(obj[3].status, ClientStatus.O.name)
        self.assertEqual(obj[3].activity, ClientActivity.TL.name)
        self.assertEqual(obj[3].details, self.a2.identifier)
        self.assertEqual(obj[4].activity, ClientActivity.AO.name)
        self.assertEqual(obj[4].details, self.a2.identifier)
        self.assertEqual(obj[5].status, ClientStatus.F.name)
        self.assertEqual(obj[5].activity, ClientActivity.HS.name)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a2.id)
        self.assertFalse(ambulance.location_client is True)


class TestMQTTHandshakeWithoutAmbulanceLogout(TestMQTT, MQTTTestCase):

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

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)
        self.assertEqual(clnt.ambulance, None)

        # check record log
        obj = ClientLog.objects.get(client=clnt)
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.HS.name)

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

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('-updated_on')[0]
        self.assertEqual(obj.status, ClientStatus.O.name)
        self.assertEqual(obj.activity, ClientActivity.AI.name)
        self.assertEqual(obj.details, self.a1.identifier)

        # Start streaming data
        test_client.publish('user/{}/ambulance/{}/data'.format(username, self.a1.id),
                            '{"location_client_id":"' + client_id + '"}', qos=2)

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertFalse(ambulance.location_client is None)
        self.assertEqual(ambulance.location_client.client_id, client_id)

        # Client handshake: offline
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)
        self.assertEqual(clnt.ambulance, None)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 6)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[0].activity, ClientActivity.HS.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)
        self.assertEqual(obj[1].activity, ClientActivity.AI.name)
        self.assertEqual(obj[1].details, self.a1.identifier)
        self.assertEqual(obj[2].status, ClientStatus.O.name)
        self.assertEqual(obj[2].activity, ClientActivity.SL.name)
        self.assertEqual(obj[2].details, self.a1.identifier)
        self.assertEqual(obj[3].status, ClientStatus.F.name)
        self.assertEqual(obj[3].activity, ClientActivity.TL.name)
        self.assertEqual(obj[3].details, self.a1.identifier)
        self.assertEqual(obj[4].status, ClientStatus.F.name)
        self.assertEqual(obj[4].activity, ClientActivity.AO.name)
        self.assertEqual(obj[4].details, self.a1.identifier)
        self.assertEqual(obj[5].status, ClientStatus.F.name)
        self.assertEqual(obj[5].activity, ClientActivity.HS.name)

        # check ambulance record
        ambulance = Ambulance.objects.get(id=self.a1.id)
        self.assertTrue(ambulance.location_client is None)


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
            'payload': 'disconnected'
        }

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake: online
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
            'payload': 'disconnected'
        }

        test_client = MQTTTestClient(broker,
                                     check_payload=False,
                                     debug=True)
        self.is_connected(test_client)

        # Client handshake: online
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

        # reconnecting with same client-id
        test_client = MQTTTestClient(broker,
                                check_payload=False,
                                debug=False)
        self.is_connected(test_client)

        # Client handshake: online
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'online')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.O.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)

        # Client handshake: offline
        test_client.publish('user/{}/client/{}/status'.format(username, client_id), 'offline')

        # process messages
        self.loop(test_client)
        subscribe_client.loop()

        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

        # check record
        clnt = Client.objects.get(client_id=client_id)
        self.assertEqual(clnt.status, ClientStatus.F.name)

        # check record log
        obj = ClientLog.objects.filter(client=clnt).order_by('updated_on')
        self.assertEqual(len(obj), 3)
        self.assertEqual(obj[0].status, ClientStatus.O.name)
        self.assertEqual(obj[1].status, ClientStatus.O.name)
        self.assertEqual(obj[2].status, ClientStatus.F.name)
