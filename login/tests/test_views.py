from django.conf import settings
from django.test import Client

from login.tests.setup_data import TestSetup


class TestViews(TestSetup):

    def test(self):

        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # logout
        client.logout()
