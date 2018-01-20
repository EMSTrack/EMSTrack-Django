import logging
import time
from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from login.models import Profile, AmbulancePermission, HospitalPermission

from login.serializers import ExtendedProfileSerializer

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability
from ambulance.serializers import AmbulanceSerializer

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType
from hospital.serializers import EquipmentSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer

from django.test import Client

from .client import MQTTTestCase, MQTTTestClient

from ..client import MQTTException
from ..subscribe import SubscribeClient
from ..publish import SingletonPublishClient

logger = logging.getLogger(__name__)

class TestMQTT():

    def is_connected(self, client, MAX_TRIES = 10):

        # connected?
        k = 0
        while not client.connected and k < MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        
    def is_subscribed(self, client, MAX_TRIES = 10):

        client.loop_start()
        
        # connected?
        k = 0
        while len(client.subscribed) and k < MAX_TRIES:
            k += 1
            time.sleep(1)
            
        client.loop_stop()
        
        self.assertEqual(len(client.subscribed), 0)
    
    def loop(self, *clients, MAX_TRIES = 10):

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
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
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
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
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
        for obj in Profile.objects.all():
            client.expect('user/{}/profile'.format(obj.user.username),
                          JSONRenderer().render(ExtendedProfileSerializer(obj).data),
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

        # Expect user profile
        profile = Profile.objects.get(user__username='testuser1')
        client.expect('user/testuser1/profile',
                      JSONRenderer().render(ExtendedProfileSerializer(profile).data),
                      qos)

        # User Ambulances
        can_read = profile.ambulances.filter(can_read=True).values('ambulance_id')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)
        
        # User Hospitals
        can_read = profile.hospitals.filter(can_read=True).values('hospital_id')
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

        # Expect user profile
        profile = Profile.objects.get(user__username='testuser2')
        client.expect('user/testuser2/profile',
                      JSONRenderer().render(ExtendedProfileSerializer(profile).data),
                      qos)

        # User Ambulances
        can_read = profile.ambulances.filter(can_read=True).values('ambulance_id')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)
        
        # User Hospitals
        can_read = profile.hospitals.filter(can_read=True).values('hospital_id')
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

    def test_mqtt_publish(self):

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
                                check_payload = False,
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
        obj = Ambulance.objects.get(id = self.a1.id)
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
        obj = Hospital.objects.get(id = self.h1.id)
        self.assertEqual(obj.comment, 'no comments')
        obj.comment = 'yet no comments'
        obj.save()
        
        # modify data in hospital_equipment and save should trigger message
        obj = HospitalEquipment.objects.get(hospital_id = self.h1.id,
                                            equipment_id = self.e1.id)
        self.assertEqual(obj.value, 'True')
        obj.value = 'False'
        obj.save()
        
        # process messages
        self.loop(client)
        client.wait()
        
        # assert changes
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'yet no comments')
        
        obj = HospitalEquipment.objects.get(hospital_id = self.h1.id,
                                            equipment_id = self.e1.id)
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
        broker['CLIENT_ID'] = 'test_mqtt_subscribe_admin'
        
        test_client = MQTTTestClient(broker,
                                     check_payload = False,
                                     debug=True)
        self.is_connected(test_client)
        
        # Modify ambulance
        
        # retrieve current ambulance status
        obj = Ambulance.objects.get(id=self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.UK.name)

        # retrive message that is there already due to creation
        test_client.expect('ambulance/{}/data'.format(self.a1.id))
        self.is_subscribed(test_client)

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
        obj = Ambulance.objects.get(id = self.a1.id)
        self.assertEqual(obj.status, AmbulanceStatus.OS.name)


        # Modify hospital
        
        # retrieve current hospital status
        obj = Hospital.objects.get(id=self.h1.id)
        self.assertEqual(obj.comment, 'no comments')
        
        # retrive message that is there already due to creation
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
        obj = Hospital.objects.get(id = self.h1.id)
        self.assertEqual(obj.comment, 'no more comments')


        # Modify hospital equipment
        
        # retrieve current equipment value
        obj = HospitalEquipment.objects.get(hospital_id=self.h1.id,
                                            equipment_id=self.e1.id)
        self.assertEqual(obj.value, 'True')
        
        # retrive message that is there already due to creation
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

        
        # wait for disconnect
        test_client.wait()
        subscribe_client.wait()

        self.assertEqual(False, True)

        
    def _test(self):
        
        

        


        


        
        
        # disconnect
        test_client.wait()
        subscribe_client.wait()
        SingletonPublishClient().wait()
        
        time.sleep(2)
