import logging

from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from django.test import Client
from rest_framework.test import APIClient

from rest_framework.parsers import JSONParser
from io import BytesIO

from login.tests.setup_data import TestSetup

from login.models import TokenLogin
from login.serializers import TokenLoginSerializer

logger = logging.getLogger(__name__)


class TestTokenLogin(TestSetup):

    def test_serializer(self):
        self.maxDiff = None

        # retrieve token
        obj = TokenLogin.objects.create(user=self.u1)
        serializer = TokenLoginSerializer(obj)
        self.assertEqual(serializer.data['url'], None)
        logger.debug(len(serializer.data['token']))
        self.assertTrue(len(serializer.data['token']) == 50)

        # create token
        data = {'username': self.u2.username}
        serializer = TokenLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        obj = TokenLogin.objects.get(user=self.u2)
        serializer = TokenLoginSerializer(obj)
        self.assertEqual(serializer.data['url'], None)
        logger.debug(len(serializer.data['token']))
        self.assertTrue(len(serializer.data['token']) == 50)

    def test_viewset(self):
        # instantiate client
        client = APIClient()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create own token
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(self.u1.username)), {}, format='json')
        self.assertEqual(response.status_code, 201)
        result = JSONParser().parse(BytesIO(response.content))

        obj = TokenLogin.objects.get(user=self.u1)
        answer = TokenLoginSerializer(obj).data
        self.assertDictEqual(result, answer)

        # create someone else's
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(self.u2.username)), {}, format='json')
        self.assertEqual(response.status_code, 404)

        # create guest
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(settings.GUEST['USERNAME'])), {}, format='json')
        self.assertEqual(response.status_code, 201)
        result = JSONParser().parse(BytesIO(response.content))

        obj = TokenLogin.objects.get(user=self.u9)
        answer = TokenLoginSerializer(obj).data
        self.assertDictEqual(result, answer)

        # create own token with url
        url = 'http://localhost/en/test/'
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(self.u1.username)), {'url': url}, format='json')
        logger.debug(response.content)
        self.assertEqual(response.status_code, 201)
        result = JSONParser().parse(BytesIO(response.content))

        obj = TokenLogin.objects.get(user=self.u1, url=url)
        answer = TokenLoginSerializer(obj).data
        self.assertDictEqual(result, answer)

        # logout
        client.logout()

    def test_login(self):

        # instantiate client
        client = APIClient()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create own token
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(self.u1.username)), {}, format='json')
        self.assertEqual(response.status_code, 201)
        token = JSONParser().parse(BytesIO(response.content))

        # logout
        client.logout()

        # instantiate client
        client = Client()

        # login with token
        response = client.get('/en/auth/login/{}/'.format(str(token['token'])), follow=True)
        logger.debug(response)
        self.assertEqual(response.status_code, 200)

        # logout
        client.logout()

    def test_login_redirect(self):
        # instantiate client
        client = APIClient()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # create own token
        # url = request.build_absolute_uri(reverse('login:login'))
        url = 'http://localhost/?next=something+other=another'
        logger.debug("url = '%s'", url)
        response = client.post('/en/api/user/{}/tokenlogin/'.format(str(self.u1.username)),
                               {'url': url},
                               format='json')
        self.assertEqual(response.status_code, 201)
        token = JSONParser().parse(BytesIO(response.content))

        # logout
        client.logout()

        # instantiate client
        client = Client()

        # login with token
        response = client.get('/en/auth/login/{}/'.format(str(token['token'])), follow=True)
        logger.debug(response)
        self.assertEqual(response.status_code, 200)

        # logout
        client.logout()

