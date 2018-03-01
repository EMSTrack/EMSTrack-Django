from ambulance.models import Call, Patient
from ambulance.serializers import CallSerializer
from emstrack.tests.util import date2iso, point2str, dict2point
from django.test import Client
from django.utils import timezone
from django.conf import settings
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from login.tests.setup_data import TestSetup

class TestCall(TestSetup):

    

    def test_call_serializer(self):
        p1 = Patient.objects.create(name="Will", age=20)
        p2 = Patient.objects.create(name="Den", age=23)
        p3 = Patient.objects.create(name="Queenie", age=21)
        c1 = Call.objects.create(number="123", street="dunno",
                updated_by=self.u1)
        c1.ambulances.add(self.a1)
        c1.ambulances.add(self.a2)
        c1.ambulances.add(self.a3)
        c1.patients.add(p1)
        c1.patients.add(p2)
        c1.patients.add(p3)

        serializer = CallSerializer(c1)
        result = {
            'id': self.c1.id,
            'acitve': self.c1.active,
            'ambulances': self.c1.ambulances,
            'patients': self.c1.patients,
            'details': self.c1.details,
            'priority': self.c1.priority,
            'comment': self.c1.comment,
            'updated_by': self.c1.updated_by.id,
            'updated_on': date2iso(self.c1.updated_on),
        }
        self.assertDictEqual(serializer.data, result)
