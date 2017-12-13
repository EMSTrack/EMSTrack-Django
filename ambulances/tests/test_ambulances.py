from django.test import TestCase, RequestFactory

from django.contrib.auth.models import User

from django.contrib.gis.geos import Point
from django.utils import timezone

from rest_framework import serializers

from ..models import Ambulance, AmbulanceCapability, AmbulanceStatus, \
    AmbulanceLocation, UserLocation, Hospital

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

    def test_ambulances(self):

        # add ambulances to users
        self.u1.profile.ambulances.add(self.a2)
        
        self.u2.profile.ambulances.add(self.a1)
        self.u2.profile.ambulances.add(self.a2)

        # u3 has no ambulances
        
        # test UserAmbulancesSerializer
        for u in (self.u1, self.u2, self.u3):
            serializer = UserAmbulancesSerializer(u.profile)
            result = []
            for e in u.profile.ambulances.all():
                result.append({ 'id': e.pk, 'identifier': e.identifier })
            self.assertEqual(serializer.data, {'ambulances': result})
        
    def test_hospitals(self):

        # add hospitals to users
        self.u1.profile.hospitals.add(self.h2)
        
        self.u2.profile.hospitals.add(self.h1)
        self.u2.profile.hospitals.add(self.h2)

        # u3 has no hospitals
        
        # test UserHospitalsSerializer
        for u in (self.u1, self.u2, self.u3):
            serializer = UserHospitalsSerializer(u.profile)
            result = []
            for e in u.profile.hospitals.all():
                result.append({ 'id': e.pk, 'name': e.name })
            self.assertEqual(serializer.data, {'hospitals': result})
        
