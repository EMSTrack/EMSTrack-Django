import time
from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

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
from ambulances.mqtt.client import MQTTException
from ambulances.mqtt.subscribe import SubscribeClient
            
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
    
    def loop(self, client, MAX_TRIES = 10):

        client.loop_start()
        
        # connected?
        k = 0
        while not client.done() and k < MAX_TRIES:
            k += 1
            time.sleep(1)
            
        client.loop_stop()
        
        self.assertEqual(client.done(), True)

class TestMQTTSeed(TestMQTT, MQTTTestCase):

    def test_mqttseed(self):

        import sys
        from django.core.management.base import OutputWrapper
        from django.core.management.color import color_style, no_style
        
        # seed
        from django.core import management
    
        management.call_command('mqttseed',
                                verbosity=1)

        print('>> Processing messages...')
        
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

        # Repeat with same client
        
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
            
        # Repeat with same client and different qos

        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
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

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser1'
        broker['PASSWORD'] = 'top_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser1'

        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
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

        # repeat with another user

        qos = 0

        # Start client as common user
        broker['USERNAME'] = 'testuser2'
        broker['PASSWORD'] = 'very_secret'
        broker['CLIENT_ID'] = 'test_mqttseed_testuser2'

        client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
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

class TestMQTTSubscribe(TestMQTT, MQTTTestCase):

    def test_mqtt_publish(self):

        import sys
        from django.core.management.base import OutputWrapper
        from django.core.management.color import color_style, no_style

        # Start client as admin
        stdout = OutputWrapper(sys.stdout)
        style = color_style()

        broker = {
            'HOST': 'localhost',
            'PORT': 1883,
            'KEEPALIVE': 60,
            'CLEAN_SESSION': True
        }
        
        # Start test client
        
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqtt_publish_admin'
        
        test_client = MQTTTestClient(broker, sys.stdout, style,
                                     verbosity = 1, strict = False,
                                     debug=True)
        self.is_connected(test_client)

        # subscribe to ambulance/+/data
        topic = 'ambulance/{}/data'.format(self.a1.id)
        test_client.expect(topic)
        self.is_subscribed(test_client)

        # process messages
        self.loop(test_client)

        print('>> Moving on...')

        # expect more
        test_client.expect(topic)

        # modify data in ambulance and save should trigger message
        a = Ambulance.objects.get(id = self.a1.id)
        a.status = AmbulanceStatus.OS.name
        a.save()
        
        # process messages
        self.loop(test_client)
        
        #answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        #self.assertDictEqual(result, answer)

    def _test_mqtt_subscribe(self):

        import sys
        from django.core.management.base import OutputWrapper
        from django.core.management.color import color_style, no_style

        # Start client as admin
        stdout = OutputWrapper(sys.stdout)
        style = color_style()

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
                                           sys.stdout,
                                           style,
                                        verbosity = 1)
        self.is_connected(subscribe_client)

        # Start test client
        
        broker.update(settings.MQTT)
        broker['CLIENT_ID'] = 'test_mqttseed_admin'
        
        test_client = MQTTTestClient(broker, sys.stdout, style, verbosity = 1)
        self.is_connected(test_client)

        # process messages
        subscribe_client.loop_start()
        test_client.loop_start()

        # Start http client

        # instantiate client
        http_client = Client()

        # login as admin and
        # retrieve ambulance via http
        http_client.login(username=settings.MQTT['USERNAME'],
                          password=settings.MQTT['PASSWORD'])
        
        response = http_client.get('/ambulances/api/ambulance/{}/'.format(str(self.a1.id)),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))

        status = AmbulanceStatus.OS.name
        test_client.publish('user/admin/ambulance/{}/data'.format(str(self.a1.id)),
                            json.dumps({
                                'status': status,
                            })
        )

        time.sleep(1)
        
        #answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        #self.assertDictEqual(result, answer)
        
        http_client.logout()
        
        # stop processing messages
        subscribe_client.loop_stop()
        test_client.loop_stop()
        
        
