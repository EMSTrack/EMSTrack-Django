from django.test import TestCase, Client

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings

from rest_framework import serializers
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from login.models import AmbulancePermission, HospitalPermission

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability
from ambulance.serializers import AmbulanceSerializer

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType
from hospital.serializers import HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer

from util.test import date2iso, point2str

class TestSetup(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Add users
        cls.u1 = User.objects.create_user(
            username=settings.MQTT['USERNAME'],
            email='admin@user.com',
            password=settings.MQTT['PASSWORD'],
            is_superuser=True)
        
        cls.u2 = User.objects.create_user(
            username='testuser1',
            email='test1@user.com',
            password='top_secret')
        
        cls.u3 = User.objects.create_user(
            username='testuser2',
            email='test2@user.com',
            password='very_secret')
        
        # Add ambulances
        cls.a1 = Ambulance.objects.create(
            identifier='BC-179',
            comment='Maintenance due',
            capability=AmbulanceCapability.B.name,
            updated_by=cls.u1)
        
        cls.a2 = Ambulance.objects.create(
            identifier='BC-180',
            comment='Need painting',
            capability=AmbulanceCapability.A.name,
            updated_by=cls.u1)

        cls.a3 = Ambulance.objects.create(
            identifier='BC-181',
            comment='Engine overhaul',
            capability=AmbulanceCapability.R.name,
            updated_by=cls.u1)
        
        # Add hospitals
        cls.h1 = Hospital.objects.create(
            name='Hospital General',
            address="Don't know",
            comment="no comments",
            updated_by=cls.u1)
        
        cls.h2 = Hospital.objects.create(
            name='Hospital CruzRoja',
            address='Forgot',
            updated_by=cls.u1)

        cls.h3 = Hospital.objects.create(
            name='Hospital Nuevo',
            address='Not built yet',
            updated_by=cls.u1)

        # add equipment
        cls.e1 = Equipment.objects.create(
            name='X-ray',
            etype=EquipmentType.B.name)

        cls.e2 = Equipment.objects.create(
            name='Beds',
            etype=EquipmentType.I.name)
        
        cls.e3 = Equipment.objects.create(
            name='MRI - Ressonance',     # name with space!
            etype=EquipmentType.B.name,
            toggleable=True)

        # add hospital equipment
        cls.he1 = HospitalEquipment.objects.create(
            hospital=cls.h1,
            equipment=cls.e1,
            value='True',
            updated_by=cls.u1)
        
        cls.he2 = HospitalEquipment.objects.create(
            hospital=cls.h1,
            equipment=cls.e2,
            value='45',
            updated_by=cls.u1)

        cls.he3 = HospitalEquipment.objects.create(
            hospital=cls.h2,
            equipment=cls.e1,
            value='False',
            updated_by=cls.u1)
        
        cls.he4 = HospitalEquipment.objects.create(
            hospital=cls.h2,
            equipment=cls.e3,
            value='True',
            updated_by=cls.u1)
        
        cls.he5 = HospitalEquipment.objects.create(
            hospital=cls.h3,
            equipment=cls.e1,
            value='True',
            updated_by=cls.u1)
        
        # add hospitals to users
        cls.u1.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=cls.h1,
                                              can_write=True),
            HospitalPermission.objects.create(hospital=cls.h3)
        )
        
        cls.u2.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=cls.h1),
            HospitalPermission.objects.create(hospital=cls.h2,
                                              can_write=True)
        )

        # u3 has no hospitals 
        
        # add ambulances to users
        cls.u1.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=cls.a2,
                                               can_write=True)
        )
        
        # u2 has no ambulances
        
        cls.u3.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=cls.a1,
                                               can_read=False),
            AmbulancePermission.objects.create(ambulance=cls.a3,
                                               can_write=True)
        )

        #print('u1: {}\n{}'.format(cls.u1, cls.u1.profile))
        #print('u2: {}\n{}'.format(cls.u2, cls.u2.profile))
        #print('u3: {}\n{}'.format(cls.u3, cls.u3.profile))

    
class TestHospitalGetList(TestSetup):

    def test_hospital_serializer(self):

        # test HospitalSerializer
        for h in (self.h1, self.h2, self.h3):
            serializer = HospitalSerializer(h)
            result = {
                'id': h.id,
                'name': h.name,
                'address': h.address,
                'location': None,
                'comment': h.comment,
                'updated_by': h.updated_by.id,
                'updated_on': date2iso(h.updated_on)
            }
            self.assertDictEqual(serializer.data, result)

    def test_hospital_get_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any hospital
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital
        response = client.get('/api/hospital/{}/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h3.id)).data
        self.assertDictEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
        
        # retrieve own's
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data
        self.assertDictEqual(result, answer)
        
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()
        
    def test_hospital_get_list_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve hospitals
        response = client.get('/api/hospital/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [HospitalSerializer(self.h1).data,
                  HospitalSerializer(self.h2).data,
                  HospitalSerializer(self.h3).data]
        self.assertCountEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve hospitals
        response = client.get('/api/hospital/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data,
            HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        ]
        self.assertCountEqual(result, answer)
        
        # logout
        client.logout()
        
        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve hospitals
        response = client.get('/api/hospital/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertCountEqual(result, answer)
        
        # logout
        client.logout()

class TestHospitalUpdate(TestSetup):
    
    def test_hospital_update_serializer(self):
        
        # superuser first
        
        # Update hospital address
        h = self.h1
        user = self.u1
        address = 'new address'
        
        serializer = HospitalSerializer(h,
                                        data={
                                            'address': address,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'comment': h.comment,
            'address': address,
            'location': point2str(h.location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        
        # Update hospital location
        location = Point(-2,7)
        
        serializer = HospitalSerializer(h,
                                        data={
                                            'location': location,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'comment': h.comment,
            'address': h.address,
            'location': point2str(location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        # regular authorized user
        
        # Update hospital address
        h = self.h2
        user = self.u2
        address = 'new address'
        
        serializer = HospitalSerializer(h,
                                        data={
                                            'address': address,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'comment': h.comment,
            'address': address,
            'location': point2str(h.location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        
        # Update hospital location
        location = Point(-2,7)
        
        serializer = HospitalSerializer(h,
                                        data={
                                            'location': location,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'comment': h.comment,
            'address': h.address,
            'location': point2str(location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on)
        }
        self.assertDictEqual(serializer.data, result)
        
    def test_hospital_patch_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve hospital
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(self.h1).data
        self.assertDictEqual(result, answer)

        # set address hospital
        address = 'new address'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve new hospital address
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['address'], address)
        
        # set hospital location
        location = Point(-2,7)
        
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'location': str(location)
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve new hospital location
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['address'], address)
        self.assertEqual(result['location'], 'SRID=4326;' + str(location))
        
        # set wrong hospital id
        response = client.patch('/api/hospital/100/',
                                data = json.dumps({
                                    'address': address
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
                
        # retrieve hospital
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(self.h2).data
        self.assertDictEqual(result, answer)

        # set address hospital
        address = 'another address'
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve new hospital address
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['address'], address)
        
        # set hospital location
        location = Point(-2,7)
        
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'location': str(location)
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve new hospital location
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['address'], address)
        self.assertEqual(result['location'], 'SRID=4326;' + str(location))
        
        # set status hospital (no permission)
        address = 'yet another hospital'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # set address hospital (no permission)
        address = 'another one address'
        response = client.patch('/api/hospital/{}/'.format(str(self.h3.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # set address hospital
        address = 'some address'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # set address hospital
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 404)

        # set address hospital
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data = json.dumps({
                                    'address': address,
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        
class TestHospitalEquipmentGetList(TestSetup):

    def test_hospital_equipment_serializer(self):

        # test HospitalSerializer
        for he in (self.he1, self.he2, self.he3, self.he4):
            serializer = HospitalEquipmentSerializer(he)
            result = {
                'hospital_id': he.hospital.id,
                'hospital_name': he.hospital.name,
                'equipment_id': he.equipment.id,
                'equipment_name': he.equipment.name,
                'equipment_etype': he.equipment.etype,
                'value': he.value,
                'comment': he.comment,
                'updated_by': he.updated_by.id,
                'updated_on': date2iso(he.updated_on)
            }
            self.assertDictEqual(serializer.data, result)

    def test_hospital_equipment_get_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e3.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h3.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve inexistent
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e2.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve own hospital equipment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e3.id)).data
        self.assertDictEqual(result, answer)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h3.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve someone else's
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e3.name)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

    def test_hospital_equipment_list_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data,
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e2.id)).data
        ]
        
        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data,
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)
        
        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h3.id,equipment=self.e1.id)).data
        ]
        self.assertCountEqual(result, answer)
        
        # retrieve inexistent
        response = client.get('/api/hospital/{}/equipment/'.format(1000),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data,
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e2.id)).data
        ]
        
        self.assertCountEqual(result, answer)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data,
            HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e3.id)).data
        ]
        self.assertCountEqual(result, answer)
        
        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve all hospital equipment
        response = client.get('/api/hospital/{}/equipment/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()


class TestHospitalEquipmentUpdate(TestSetup):

    def test_hospital_equipment_update_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # set equipment value
        value = 'True'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'value': value
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve equipment value
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        
        # set equipment comment
        comment = 'some comment'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'comment': comment
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h1.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve equipment comment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        self.assertEqual(result['comment'], comment)

        # set inexistent equipment
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e3.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'comment': comment
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # set wrong ambulance id
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id+100), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'comment': comment
                                })
        )
        self.assertEqual(response.status_code, 404)

        # set wrong equipment name
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name+'wrong')),
                                content_type='application/json',
                                data = json.dumps({
                                    'comment': comment
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
        
        # set equipment value
        value = 'False'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'value': value
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve equipment value
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        
        # set equipment comment
        comment = 'some new comment'
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'comment': comment
                                })
        )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalEquipmentSerializer(HospitalEquipment.objects.get(hospital=self.h2.id,equipment=self.e1.id)).data
        self.assertDictEqual(result, answer)
        
        # retrieve equipment comment
        response = client.get('/api/hospital/{}/equipment/{}/'.format(str(self.h2.id), str(self.e1.name)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['value'], value)
        self.assertEqual(result['comment'], comment)

        # not permitted to write
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'value': value
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()
        
        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # set equipment value
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e1.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'value': value
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # set equipment value
        response = client.patch('/api/hospital/{}/equipment/{}/'.format(str(self.h1.id), str(self.e2.name)),
                                content_type='application/json',
                                data = json.dumps({
                                    'value': value
                                })
        )
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

class TestHospitalEquipmentMetadata(TestSetup):
        
    def test_hospital_equipment_metadata_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e2.id)).data
            ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e3.id)).data
            ]
        self.assertCountEqual(result, answer)
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data
            ]
        self.assertCountEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e2.id)).data
            ]
        self.assertCountEqual(result, answer)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [
            EquipmentSerializer(Equipment.objects.get(id=self.e1.id)).data,
            EquipmentSerializer(Equipment.objects.get(id=self.e3.id)).data
            ]
        self.assertCountEqual(result, answer)
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h2.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve any hospital equipment
        response = client.get('/api/hospital/{}/metadata/'.format(str(self.h3.id)),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()
        
