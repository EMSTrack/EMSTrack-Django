import json
import logging
import tablib
from io import BytesIO

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.test import Client as DjangoClient
from rest_framework.parsers import JSONParser

from ambulance.models import Ambulance
from emstrack.tests.util import date2iso
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from login.resources import UserResource
from login.serializers import ClientSerializer
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestUserResource(TestSetup):

    def setUp(self):

        # call super
        super().setUp()

        self.resource = UserResource()

        self.dataset = tablib.Dataset(headers=['id', 'username', 'first_name', 'last_name', 'email', 'mobile_number',
                                               'is_staff', 'is_dispatcher', 'is_active'])
        row = [self.u5.id, 'change', 'first', 'last', 'email@email.com', '+15555050505', False, True, True]
        self.dataset.append(row)

    def test_get_instance(self):
        instance_loader = self.resource._meta.instance_loader_class(self.resource)
        self.resource._meta.import_id_fields = ['id']

        instance = self.resource.get_instance(instance_loader,
                                              self.dataset.dict[0])
        self.assertEqual(instance, self.u5)
