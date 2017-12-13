from django.test import TestCase, RequestFactory

from django.contrib.auth.models import User

from django.contrib.gis.geos import Point
from django.utils import timezone

from rest_framework import serializers

from ..models import Ambulance, AmbulanceCapability, AmbulanceStatus, \
    AmbulanceLocation, UserLocation

from ..serializers import UserAmbulancesSerializer, UserHospitalsSerializer
# AmbulanceStatusSerializer, \
#    AmbulanceCapabilitySerializer, AmbulanceSerializer, \
#    UserLocationSerializer

from django.test import Client

class CreateAmbulance(TestCase):

    def setUp(self):

        # Add status
        self.s1 = AmbulanceStatus.objects.create(name='Out of service')
        self.s2 = AmbulanceStatus.objects.create(name='In service')
        self.s3 = AmbulanceStatus.objects.create(name='Available')
        
        # Add capability
        self.c1 = AmbulanceCapability.objects.create(name='Basic')
        self.c2 = AmbulanceCapability.objects.create(name='Advanced')
        self.c3 = AmbulanceCapability.objects.create(name='Rescue')
        
        # Add ambulances
        self.a1 = Ambulance.objects.create(
            identifier='BC-179',
            comment='Maintenance due',
            capability=self.c1)
        
        self.a2 = Ambulance.objects.create(
            identifier='BC-180',
            comment='Need painting',
            capability=self.c2)

        self.a3 = Ambulance.objects.create(
            identifier='BC-181',
            comment='Engine overhaul',
            capability=self.c3)
        
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

        # Add UserLocation
        self.t1 = timezone.now()
        self.ul1 = UserLocation.objects.create(user=self.u1,
                                               location=Point(1,1),
                                               timestamp=self.t1)
        
        # Add UserLocation
        self.t2 = timezone.now()
        self.ul2 = UserLocation.objects.create(user=self.u2,
                                               location=Point(3,-1),
                                               timestamp=self.t2)

    def test_hospitals(self):

        # add ambulances
        self.u2.profile.ambulances.add(self.a1)
        self.u2.profile.ambulances.add(self.a2)
        
        self.u3.profile.ambulances.add(self.a3)
        
        # test UserAmbulancesSerializer
        for u in (self.u1, self.u2, self.u3):
            serializer = UserAmbulancesSerializer(u)
            result = []
            for e in u.profile.ambulances:
                result.add({ 'id': e.pk, 'identifier': e.identifier })
            self.assertEqual(serializer.data, result)
        
    def dtest_ambulances(self):

        # test AmbulanceStatusSerializer
        for s in (self.s1, self.s2, self.s3):
            serializer = AmbulanceStatusSerializer(s)
            result = [{ 'id': s.pk, 'name': s.name }]
            self.assertEqual(serializer.data, result)

        # test AmbulanceCapabilitySerializer
        for c in (self.c1, self.c2, self.c3):
            serializer = AmbulanceCapabilitySerializer(c)
            result = { 'id': c.pk, 'name': c.name }
            self.assertEqual(serializer.data, result)
            
        # test AmbulanceSerializer
        for a in (self.a1, self.a2):
            serializer = AmbulanceSerializer(a)
            result = { 'id': a.pk,
                       'identifier': a.identifier,
                       'comment': a.comment, 
                       'capability': a.capability.name,
                       'updated_at': None,
                       'location': None}
            self.assertEqual(serializer.data, result)
        
        # test UserLocationSerializer
        for ul in (self.ul1, self.ul2):
            serializer = UserLocationSerializer(ul)
            data = { 'user_id': ul.user,
                     'latitude': ul.location.y,
                     'longitude': ul.location.x,
                     'timestamp': ul.timestamp}
            result = UserLocationSerializer(data=result)
            self.assertEqual(result.is_valid(), True)
            self.assertEqual(serializer.data, result.validated_data)
            
        # # Location
        # time = timezone.now()
        # AmbulanceLocation(location=UserLocation(user=self.u1,
        #                                         location=Point(1,1),
        #                                         timestamp=time),
        #                   status=self.s1,
        #                   orientation=0.0)
