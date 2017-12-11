from django.test import TestCase, RequestFactory

from django.contrib.auth.models import User

from django.contrib.gis.geos import Point
from django.utils import timezone

from ..models import Ambulance, AmbulanceCapability, AmbulanceStatus

from ..serializers import AmbulanceStatusSerializer, \
    AmbulanceCapabilitySerializer, AmbulanceSerializer

from django.test import Client

class CreateAmbulance(TestCase):

    def setUp(self):

        # Add status
        self.s1 = AmbulanceStatus(name='Out of service')
        self.s1.save()
        self.s2 = AmbulanceStatus(name='In service')
        self.s2.save()
        self.s3 = AmbulanceStatus(name='Available')
        self.s3.save()
        
        # Add capability
        self.c1 = AmbulanceCapability(name='Basic')
        self.c1.save()
        self.c2 = AmbulanceCapability(name='Advanced')
        self.c2.save()
        self.c3 = AmbulanceCapability(name='Rescue')
        self.c3.save()
        
        # Add ambulances
        self.a1 = Ambulance(
            identifier='BC-179',
            comment='Maintenance due',
            capability=self.c1)
        
        # Add ambulances
        self.a2 = Ambulance(
            identifier='BC-180',
            comment='Need painting',
            capability=self.c2)

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
        
    def test_ambulances(self):

        # test AmbulanceStatusSerializer
        for s in (self.s1, self.s2, self.s3):
            serializer = AmbulanceStatusSerializer(s)
            result = { 'id': s.pk, 'name': s.name }
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
        
        # Location
        time = timezone.now()
        AmbulanceLocation(location=UserLocation(user=self.u1,
                                                location=Point(1,1),
                                                timestamp=time),
                          status=self.s1,
                          orientation=0.0)
