from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from django.contrib.gis.geos import Point
from django.utils import timezone

from rest_framework import serializers

from ambulances.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability, \
    AmbulancePermission, HospitalPermission, \
    Hospital, \
    Equipment, HospitalEquipment, EquipmentType

from ambulances.serializers import ProfileSerializer, \
    AmbulanceSerializer, ExtendedProfileSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer, \
    EquipmentSerializer

from django.test import Client

def date2iso(date):
    if date is not None:
        return date.isoformat().replace('+00:00','Z')
    return date

def point2str(point):
    #return 'SRID=4326;' + str(point)
    if point is not None:
        return str(point)
    return point

import subprocess

class LiveTestSetup(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # determine server and port
        host, port = self.live_server_url.split(':')
        
        # stop mosquito server
        retval = subprocess.run(["service", "stop", "mosquito"])

        # change default host and port
        cat = subprocess.check_output(["cat", "/etc/mosquitto/conf.d/default.conf"]))
        sed1 = subprocess.check_output(["sed", "s/127.0.0.1/{}".format(host), "/etc/mosquitto/conf.d/default.conf"], stdin=cat))
        sed2 = subprocess.check_output(["sed", "s/8000/{}".format(port)], stdin=sed1))
        print('sed2 = {}'.format(sed2))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):

        # Add users
        cls.u1 = User.objects.create_user(
            username='admin',
            email='admin@user.com',
            password='admin',
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


class TestMQTTSeed(LiveTestSetup):
        
    def test_mqttseed(self):
        
        from django.core import management

        print('server address = {}'.format(self.live_server_url))
        
        #management.call_command('mqttseed',
        #                        verbosity=0)

        print('done')
        
