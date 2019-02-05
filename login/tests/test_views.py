import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client

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
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create user
        response = self.client.post('/auth/user/create/',
                                    {'username': "LatestTest",
                                     'password1': 'pass1234pass',
                                     'password2': 'pass1234pass',
                                     })
        self.assertEqual(response.status_code, 200)
        logger.debug(response.body)
        self.assertEqual(User.objects.last().username, "LatestTest")

        # logout
        client.logout()
