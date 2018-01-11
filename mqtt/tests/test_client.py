import time
from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from login.models import Profile, AmbulancePermission, HospitalPermission

from login.serializers import ExtendedProfileSerializer

from ambulance.models import Ambulance, \
    AmbulanceStatus, AmbulanceCapability
from ambulance.serializers import AmbulanceSerializer

from hospital.models import Hospital, \
    Equipment, HospitalEquipment, EquipmentType
from hospital.serializers import EquipmentSerializer, \
    HospitalSerializer, HospitalEquipmentSerializer

from django.test import Client

from .client import MQTTTestCase, MQTTTestClient

from ..client import MQTTException
from ..subscribe import SubscribeClient
            
class TestMQTTSeed(TestMQTT, MQTTTestCase):

    def test_mqttseed(self):

        self.assertEqual(True, True)
