from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType

class TestSetupData():

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

class TestSetup(TestSetupData, TestCase):
    pass
