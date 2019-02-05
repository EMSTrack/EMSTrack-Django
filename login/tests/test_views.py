import logging
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rest_framework.parsers import JSONParser

from ambulance.models import Ambulance
from ambulance.serializers import AmbulanceSerializer
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestModels(TestSetup):

    def test(self):

        # Do all users have a userprofile?
        self.assertIsNotNone(self.u1.userprofile)
        self.assertIsNotNone(self.u2.userprofile)
        self.assertIsNotNone(self.u3.userprofile)
        self.assertIsNotNone(self.u4.userprofile)
        self.assertIsNotNone(self.u5.userprofile)
        self.assertIsNotNone(self.u6.userprofile)
        self.assertIsNotNone(self.u7.userprofile)
        self.assertIsNotNone(self.u8.userprofile)

        # Do all groups have a groupprofile?
        self.assertIsNotNone(self.g1.groupprofile)
        self.assertIsNotNone(self.g2.groupprofile)
        self.assertIsNotNone(self.g3.groupprofile)
        self.assertIsNotNone(self.g4.groupprofile)
        self.assertIsNotNone(self.g5.groupprofile)
        self.assertIsNotNone(self.g6.groupprofile)


class TestViews(TestSetup):

    def test(self):

        # instantiate client
        client = Client()

        # login as admin
        login = client.login(username=settings.MQTT['USERNAME'],
                             password=settings.MQTT['PASSWORD'])
        self.assertTrue(login)

        # retrieve any ambulance
        response = client.get('/api/ambulance/{}/'.format(str(self.a1.id)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = AmbulanceSerializer(Ambulance.objects.get(id=self.a1.id)).data
        self.assertDictEqual(result, answer)

        # user detail
        response = self.client.post(reverse('login:detail-user', kwargs={'pk': self.u1.id}),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        logger.debug(response.content)
        self.assertTrue(False)

        # logout
        client.logout()
