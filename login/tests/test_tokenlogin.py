import logging

from django.test import Client
from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from rest_framework.parsers import JSONParser
from io import BytesIO

from login.tests.setup_data import TestSetup

from login.models import TokenLogin
from login.serializers import TokenLoginSerializer

logger = logging.getLogger(__name__)


class TestTokenLogin(TestSetup):

    def test_serializer(self):
        self.maxDiff = None

        u = self.u1
        obj = TokenLogin.objects.create(user=u)

        serializer = TokenLoginSerializer(obj)
        self.assertEqual(serializer.data['url'], None)
        logger.debug(len(serializer.data['token']))
        self.assertTrue(len(serializer.data['token']) == 50)

    def test_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve own
        response = client.get('/en/api/tokenlogin/{}/'.format(str(self.u1.username)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))

        obj = TokenLogin.objects.get(user=self.u1)
        answer = TokennLoginSerializer(obj).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/en/api/tokenlogin/{}/'.format(str(self.u2.username)),
                              follow=True)
        self.assertEqual(response.status_code, 404)

        # logout
        client.logout()
