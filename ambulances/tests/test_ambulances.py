from django.test import TestCase, RequestFactory

from django.contrib.auth.models import User

from django.contrib.gis.geos import Point
from django.utils import timezone

from rest_framework import serializers

from ambulances.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability, \
    AmbulancePermission, HospitalPermission, \
    AmbulanceUpdate, Hospital

from ambulances.serializers import ProfileSerializer, \
    AmbulanceSerializer
#    AmbulanceCapabilitySerializer, AmbulanceSerializer, \
#    UserLocationSerializer

import collections

from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from django.test import Client

class CreateAmbulance(TestCase):

    def setUp(self):

        # Add ambulances
        self.a1 = Ambulance.objects.create(
            identifier='BC-179',
            comment='Maintenance due',
            capability=AmbulanceCapability.B.name)
        
        self.a2 = Ambulance.objects.create(
            identifier='BC-180',
            comment='Need painting',
            capability=AmbulanceCapability.A.name)

        self.a3 = Ambulance.objects.create(
            identifier='BC-181',
            comment='Engine overhaul',
            capability=AmbulanceCapability.R.name)
        
        # Add hospitals
        self.h1 = Hospital.objects.create(
            name='Hospital General',
            address="Don't know")
        
        self.h2 = Hospital.objects.create(
            name='Hospital CruzRoja',
            address='Forgot')

        self.h3 = Hospital.objects.create(
            name='Hospital Nuevo',
            address='Not built yet')
        
        # Add users
        self.u1 = User.objects.create_user(
            username='admin',
            email='admin@user.com',
            password='admin',
            is_superuser=True)
        
        self.u2 = User.objects.create_user(
            username='testuser1',
            email='test1@user.com',
            password='top_secret')
        
        self.u3 = User.objects.create_user(
            username='testuser2',
            email='test2@user.com',
            password='very_secret')

        # add hospitals to users
        self.u1.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=self.h1,
                                              can_write=True),
            HospitalPermission.objects.create(hospital=self.h3)
        )
        
        self.u2.profile.hospitals.add(
            HospitalPermission.objects.create(hospital=self.h1),
            HospitalPermission.objects.create(hospital=self.h2,
                                              can_write=True)
        )

        # u3 has no hospitals 
        
        # add ambulances to users
        self.u1.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=self.a2,
                                               can_write=True)
        )
        
        # u2 has no ambulances
        
        self.u3.profile.ambulances.add(
            AmbulancePermission.objects.create(ambulance=self.a1,
                                               can_read=False),
            AmbulancePermission.objects.create(ambulance=self.a3,
                                               can_write=True)
        )
        
        # # Add UserLocation
        # self.t1 = timezone.now()
        # self.ul1 = UserLocation.objects.create(user=self.u1,
        #                                        location=Point(1,1),
        #                                        timestamp=self.t1)
        
        # # Add UserLocation
        # self.t2 = timezone.now()
        # self.ul2 = UserLocation.objects.create(user=self.u2,
        #                                        location=Point(3,-1),
        #                                        timestamp=self.t2)

    def test_profile_serializer(self):

        # test ProfileSerializer
        for u in (self.u1, self.u2, self.u3):
            serializer = ProfileSerializer(u.profile)
            result = {
                'ambulances': [
                    {
                        'ambulance_id': e.ambulance.pk,
                        'ambulance_identifier': e.ambulance.identifier,
                        'can_read': e.can_read,
                        'can_write': e.can_write
                    }
                    for e in u.profile.ambulances.all()
                ],
                'hospitals': [
                    {
                        'hospital_id': e.hospital.pk,
                        'hospital_name': e.hospital.name,
                        'can_read': e.can_read,
                        'can_write': e.can_write
                    }
                    for e in u.profile.hospitals.all()
                ]
            }
            self.assertDictEqual(serializer.data, result)
            

    def test_profile_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username='admin', password='admin')

        # retrieve own
        response = client.get('/ambulances/api/profile/' + str(self.u1.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ProfileSerializer(self.u1.profile).data
        self.assertDictEqual(result, answer)
        
        # retrieve someone else's
        response = client.get('/ambulances/api/profile/' + str(self.u2.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ProfileSerializer(self.u2.profile).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/ambulances/api/profile/' + str(self.u3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ProfileSerializer(self.u3.profile).data
        self.assertDictEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
        
        # retrieve own
        response = client.get('/ambulances/api/profile/' + str(self.u2.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = ProfileSerializer(self.u2.profile).data
        self.assertDictEqual(result, answer)
        
        # retrieve someone else's
        response = client.get('/ambulances/api/profile/' + str(self.u1.id),
                              follow=True)
        self.assertEqual(response.status_code, 403)
        
        response = client.get('/ambulances/api/profile/' + str(self.u3.id),
                              follow=True)
        self.assertEqual(response.status_code, 403)
        
        # logout
        client.logout()

    def test_ambulance_serializer(self):

        # test AmbulanceSerializer
        for a in (self.a1, self.a2, self.a3):
            serializer = AmbulanceSerializer(a)
            result = {
                'id': a.pk,
                'identifier': a.identifier,
                'comment': a.comment,
                'capability': a.capability,
                'status': None,
                'location': a.location,
                'updated_on': a.updated_on.isoformat(timespec='microseconds').replace('+00:00', 'Z'),
            }
            if a.location:
                result['status'] = a.location.status
            self.assertDictEqual(serializer.data, result)
        
    def test_ambulance_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username='admin', password='admin')

        # retrieve any ambulance
        response = client.get('/ambulances/api/ambulance/' + str(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a1).data
        self.assertDictEqual(result, answer)

        # retrieve any ambulance
        response = client.get('/ambulances/api/ambulance/' + str(self.a2.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a2).data
        self.assertDictEqual(result, answer)

        # retrieve any ambulance
        response = client.get('/ambulances/api/ambulance/' + str(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a3).data
        self.assertDictEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser2
        client.login(username='testuser2', password='very_secret')
        
        # retrieve own
        response = client.get('/ambulances/api/ambulance/' + str(self.a3.id),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(self.a3).data
        self.assertDictEqual(result, answer)
        
        # retrieve someone else's
        response = client.get('/ambulances/api/ambulance/' + str(self.a2.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # can't read
        response = client.get('/ambulances/api/ambulance/' + str(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')
        
        # retrieve someone else's
        response = client.get('/ambulances/api/ambulance/' + str(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # retrieve someone else's
        response = client.get('/ambulances/api/ambulance/' + str(self.a2.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        response = client.get('/ambulances/api/ambulance/' + str(self.a1.id),
                              follow=True)
        self.assertEqual(response.status_code, 404)
        
        # logout
        client.logout()
        
    def test_ambulance_list_viewset(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username='admin', password='admin')

        # retrieve ambulances
        response = client.get('/ambulances/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [AmbulanceSerializer(self.a1).data,
                  AmbulanceSerializer(self.a2).data,
                  AmbulanceSerializer(self.a3).data]
        self.assertEqual(result, answer)
        
        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve ambulances
        response = client.get('/ambulances/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = []
        self.assertEqual(result, answer)
        
        # logout
        client.logout()
        
        # login as testuser2
        client.login(username='testuser2', password='very_secret')

        # retrieve ambulances
        response = client.get('/ambulances/api/ambulance/',
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = [ # AmbulanceSerializer(self.a1).data, # can't read
                  AmbulanceSerializer(self.a3).data]
        self.assertEqual(result, answer)
        
        # logout
        client.logout()
