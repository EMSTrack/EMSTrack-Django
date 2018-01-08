import time
from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.renderers import JSONRenderer

from ambulances.models import Profile, Ambulance, \
    AmbulanceStatus, AmbulanceCapability, \
    AmbulancePermission, HospitalPermission, \
    Hospital, \
    Equipment, HospitalEquipment, EquipmentType

from ambulances.serializers import ProfileSerializer, \
    AmbulanceSerializer, ExtendedProfileSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer, \
    EquipmentSerializer

from django.test import Client

from ambulances.tests.mqtt import MQTTTestCase, MQTTTestClient
from ambulances.mqttclient import MQTTException
            
class TestMQTTSeed(MQTTTestCase):

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
    
    def loop(self, client, MAX_TRIES = 10):

        client.loop_start()
        
        # connected?
        k = 0
        while not client.done() and k < MAX_TRIES:
            k += 1
            time.sleep(1)
            
        client.loop_stop()
        
        self.assertEqual(client.done(), True)
        
    def test_mqttseed(self):

        import sys
        from django.core.management.base import OutputWrapper
        from django.core.management.color import color_style, no_style
        
        # seed
        from django.core import management
    
        management.call_command('mqttseed',
                                verbosity=1)
        
        # Start client as admin
        stdout = OutputWrapper(sys.stdout)
        style = color_style()

        # Instantiate broker
        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqttseed_admin'
        
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)

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

    def _test(self):
        
        # Repeat with same client
        
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

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
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        process_messages(client)
        self.assertEqual(client.done(), True)
        print('<< done')
            
        # Repeat with same client and different qos

        qos = 2
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        self.assertEqual(client.connected, True)
        
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
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        process_messages(client)
        self.assertEqual(client.done(), True)
        print('<< done')

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1'

        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        # connected?
        k = 0
        while not client.connected and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(client.connected, True)
        print('>> connected')

        self.assertEqual(client.connected, True)
        
        # Expect user profile
        profile = Profile.objects.get(user__username='testuser1')
        client.expect('user/testuser1/profile',
                      JSONRenderer().render(ExtendedProfileSerializer(profile).data),
                      qos)

        # Ambulances
        can_read = profile.ambulances.filter(can_read=True).values('ambulance_id')
        for ambulance in Ambulance.objects.filter(id__in=can_read):
            client.expect('ambulance/{}/data'.format(ambulance.id),
                          JSONRenderer().render(AmbulanceSerializer(ambulance).data),
                          qos)
        
        # Hospitals
        can_read = profile.hospitals.filter(can_read=True).values('hospital_id')
        for hospital in Hospital.objects.filter(id__in=can_read):
            client.expect('hospital/{}/data'.format(hospital.id),
                          JSONRenderer().render(HospitalSerializer(hospital).data),
                          qos)
            
        # Expect all hospital equipments
        for e in HospitalEquipment.objects.filter(hospital__id__in=can_read):
            client.expect('hospital/{}/equipment/{}/data'.format(e.hospital.id,
                                                                 e.equipment.name),
                          JSONRenderer().render(HospitalEquipmentSerializer(e).data),
                          qos)

        # Subscribed?
        k = 0
        while len(client.subscribed) and k < self.MAX_TRIES:
            k += 1
            client.loop()

        self.assertEqual(len(client.subscribed), 0)
        print('>> subscribed')

        # Process all messages
        process_messages(client)
        self.assertEqual(client.done(), True)
        print('<< done')
        
    def _test(self):

        print('<< testuser1')
        
            
        try:
        
            client.loop_start()
        
            while not client.connected or not client.done():
                print('connected = {}, done = {}'.format(client.connected,
                                                         client.done()))
                print('subscribed = {}'.format(client.subscribed))
                time.sleep(1)
            
            self.assertEqual(client.connected, True)

            client.loop_stop()
            
        except KeyboardInterrupt:
            pass
        
        finally:
            client.disconnect()

    def _test(self):
            
        # Start client as common user with wrong password
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secreto'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1_wrong'

        # with self.assertRaises():
        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        client.test = self

        with self.assertRaises(MQTTException) as cm:
            while True:
                client.loop()
        
        self.assertEqual(client.connected, False)
        self.assertEqual(cm.exception.value, 5)

        client.disconnect()
        
