from django.test import TestCase

from django.contrib.auth.models import User, Group
from django.conf import settings

from login.models import \
    GroupHospitalPermission, GroupAmbulancePermission, \
    UserHospitalPermission, UserAmbulancePermission

from ambulance.models import Ambulance, \
    AmbulanceCapability, Location, LocationType

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType


class TestSetupData:

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

        cls.u4 = User.objects.create_user(
            username='testuser3',
            email='test3@user.com',
            password='highly_secret')

        cls.u5 = User.objects.create_user(
            username='testuser4',
            email='test4@user.com',
            password='extremely_secret')

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
            number="1234",
            street="don't know",
            comment="no comments",
            updated_by=cls.u1)

        cls.h2 = Hospital.objects.create(
            name='Hospital CruzRoja',
            number="4321",
            street='Forgot',
            updated_by=cls.u1)

        cls.h3 = Hospital.objects.create(
            name='Hospital Nuevo',
            number="0000",
            street='Not built yet',
            updated_by=cls.u1)

        # add equipment
        cls.e1 = Equipment.objects.create(
            name='X-ray',
            type=EquipmentType.B.name)

        cls.e2 = Equipment.objects.create(
            name='Beds',
            type=EquipmentType.I.name)

        cls.e3 = Equipment.objects.create(
            name='MRI - Ressonance',  # name with space!
            type=EquipmentType.B.name)

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
        UserHospitalPermission.objects.create(user=cls.u1,
                                              hospital=cls.h1,
                                              can_write=True)
        UserHospitalPermission.objects.create(user=cls.u1,
                                              hospital=cls.h3)

        UserHospitalPermission.objects.create(user=cls.u2,
                                              hospital=cls.h1)
        UserHospitalPermission.objects.create(user=cls.u2,
                                              hospital=cls.h2,
                                              can_write=True)

        # u3 has no hospitals 

        # add ambulances to users
        UserAmbulancePermission.objects.create(user=cls.u1,
                                               ambulance=cls.a2,
                                               can_write=True)

        # u2 has no ambulances

        UserAmbulancePermission.objects.create(user=cls.u3,
                                               ambulance=cls.a1,
                                               can_read=False)
        UserAmbulancePermission.objects.create(user=cls.u3,
                                               ambulance=cls.a3,
                                               can_write=True)

        # Create groups
        cls.g1 = Group.objects.create(name='EMTs')
        cls.g2 = Group.objects.create(name='Drivers')
        cls.g3 = Group.objects.create(name='Dispatcher')
        cls.g4 = Group.objects.create(name='NoAccessUser')
        print(cls.g4.)

        # add hospitals to groups
        GroupHospitalPermission.objects.create(group=cls.g1,
                                               hospital=cls.h1,
                                               can_write=True)
        GroupHospitalPermission.objects.create(group=cls.g1,
                                               hospital=cls.h3)

        GroupHospitalPermission.objects.create(group=cls.g2,
                                               hospital=cls.h1)
        GroupHospitalPermission.objects.create(group=cls.g2,
                                               hospital=cls.h2,
                                               can_write=True)

        # g3 has no hospitals

        # g4 has no hospitals

        # add ambulances to groups
        GroupAmbulancePermission.objects.create(group=cls.g1,
                                                ambulance=cls.a2,
                                                can_write=True)

        # g2 has no ambulances

        GroupAmbulancePermission.objects.create(group=cls.g3,
                                                ambulance=cls.a1,
                                                can_read=False)
        GroupAmbulancePermission.objects.create(group=cls.g3,
                                                ambulance=cls.a3,
                                                can_write=True)

        # g4 has no ambulances

        cls.u4.groups.set([cls.g2])
        cls.u5.groups.set([cls.g1, cls.g3])

        # Locations
        cls.l1 = Location.objects.create(
            name='AED 1',
            type=LocationType.a.name,
            number="1234",
            street="don't know",
            comment="no comments",
            updated_by=cls.u1)

        cls.l2 = Location.objects.create(
            name='Base 1',
            type=LocationType.b.name,
            number="4321",
            street='Forgot',
            updated_by=cls.u1)

        cls.l3 = Location.objects.create(
            name='AED 2',
            type=LocationType.a.name,
            number="0000",
            street='Not built yet',
            updated_by=cls.u1)


class TestSetup(TestSetupData, TestCase):
    pass
