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
        c1 = Call.objects.create(
        number="123",
        street="dunno",
        updated_by=self.u1)

        serializer = CallSerializer(c1)
        result = {
            'id': c1.id,
            'number': c1.number,
            'street': c1.street,
            'acitve': c1.active,
            'details': c1.details,
            'priority': c1.priority,
            'created_at': date2iso(c1.created_at),
            'ended_at': date2iso(c1.ended_at),
            'comment': c1.comment,
            'updated_by': c1.updated_by.id,
            'updated_on': date2iso(c1.updated_on),
        }
        self.assertDictEqual(serializer.data, result)
