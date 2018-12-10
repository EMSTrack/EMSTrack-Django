import logging

from django.test import Client

from django.conf import settings

from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from hospital.models import Hospital
from equipment.models import EquipmentItem
from hospital.serializers import HospitalSerializer
from equipment.serializers import EquipmentItemSerializer

from emstrack.tests.util import date2iso, point2str

from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestHospitalGetList(TestSetup):

    def test_hospital_serializer(self):
        # test HospitalSerializer
        for h in (self.h1, self.h2, self.h3):
            serializer = HospitalSerializer(h)
            result = {
                'id': h.id,
                'name': h.name,
                'number': h.number,
                'street': h.street,
                'unit': h.unit,
                'neighborhood': h.neighborhood,
                'city': h.city,
                'state': h.state,
                'zipcode': h.zipcode,
                'country': h.country,
                'location': point2str(h.location),
                'comment': h.comment,
                'updated_by': h.updated_by.id,
                'updated_on': date2iso(h.updated_on),
                'hospitalequipment_set': 
                    EquipmentItemSerializer(EquipmentItem.objects.filter(equipment_holder_id=h.equipment.id), 
                                            many=True).data
            }
            logger.debug('answer= {}'.format(serializer.data))
            logger.debug('result = {}'.format(result))
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

        # Update hospital street
        h = self.h1
        user = self.u1
        street = 'new street'

        serializer = HospitalSerializer(h,
                                        data={
                                            'street': street,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'number': h.number,
            'street': street,
            'unit': h.unit,
            'neighborhood': h.neighborhood,
            'city': h.city,
            'state': h.state,
            'zipcode': h.zipcode,
            'country': h.country,
            'comment': h.comment,
            'location': point2str(h.location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on),
            'hospitalequipment_set':
                EquipmentItemSerializer(EquipmentItem.objects.filter(equipment_holder_id=h.equipment.id),
                                        many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # Update hospital location
        location = {'latitude': -2., 'longitude': 7.}

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
            'number': h.number,
            'street': h.street,
            'unit': h.unit,
            'neighborhood': h.neighborhood,
            'city': h.city,
            'state': h.state,
            'zipcode': h.zipcode,
            'country': h.country,
            'comment': h.comment,
            'location': point2str(location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on),
            'hospitalequipment_set':
                EquipmentItemSerializer(EquipmentItem.objects.filter(equipment_holder_id=h.equipment.id),
                                        many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # regular authorized user

        # Update hospital street
        h = self.h2
        user = self.u2
        street = 'new street'

        serializer = HospitalSerializer(h,
                                        data={
                                            'street': street,
                                        }, partial=True)
        serializer.is_valid()
        serializer.save(updated_by=user)

        # test
        serializer = HospitalSerializer(h)
        result = {
            'id': h.id,
            'name': h.name,
            'number': h.number,
            'street': street,
            'unit': h.unit,
            'neighborhood': h.neighborhood,
            'city': h.city,
            'state': h.state,
            'zipcode': h.zipcode,
            'country': h.country,
            'comment': h.comment,
            'location': point2str(h.location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on),
            'hospitalequipment_set':
                EquipmentItemSerializer(EquipmentItem.objects.filter(equipment_holder_id=h.equipment.id),
                                        many=True).data
        }
        self.assertDictEqual(serializer.data, result)

        # Update hospital location
        location = {'latitude': -2., 'longitude': 7.}

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
            'number': h.number,
            'street': h.street,
            'unit': h.unit,
            'neighborhood': h.neighborhood,
            'city': h.city,
            'state': h.state,
            'zipcode': h.zipcode,
            'country': h.country,
            'comment': h.comment,
            'location': point2str(location),
            'updated_by': user.id,
            'updated_on': date2iso(h.updated_on),
            'hospitalequipment_set':
                EquipmentItemSerializer(EquipmentItem.objects.filter(equipment_holder_id=h.equipment.id),
                                        many=True).data
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

        # set street hospital
        street = 'new street'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h1.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new hospital street
        response = client.get('/api/hospital/{}/'.format(str(self.h1.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['street'], street)

        # set hospital location
        location = {'latitude': -2., 'longitude': 7.}

        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data=json.dumps({
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
        self.assertEqual(result['street'], street)
        self.assertEqual(result['location'], point2str(location))

        # set wrong hospital id
        response = client.patch('/api/hospital/100/',
                                data=json.dumps({
                                    'street': street
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

        # set street hospital
        street = 'another street'
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = HospitalSerializer(Hospital.objects.get(id=self.h2.id)).data
        self.assertDictEqual(result, answer)

        # retrieve new hospital street
        response = client.get('/api/hospital/{}/'.format(str(self.h2.id)))
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(result['street'], street)

        # set hospital location
        location = {'latitude': -2., 'longitude': 7.}

        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'location': point2str(location)
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
        self.assertEqual(result['street'], street)
        self.assertEqual(result['location'], point2str(location))

        # set status hospital (no permission)
        street = 'yet another hospital'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # set street hospital (no permission)
        street = 'another one street'
        response = client.patch('/api/hospital/{}/'.format(str(self.h3.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # set street hospital
        street = 'some street'
        response = client.patch('/api/hospital/{}/'.format(str(self.h1.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # set street hospital
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # set street hospital
        response = client.patch('/api/hospital/{}/'.format(str(self.h2.id)),
                                content_type='application/json',
                                data=json.dumps({
                                    'street': street,
                                })
                                )
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()


