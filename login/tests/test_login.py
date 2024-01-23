import logging

from django.test import Client
from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework.parsers import JSONParser
from io import BytesIO

from ambulance.models import Ambulance

from hospital.models import Hospital

from ..models import TemporaryPassword

from ..serializers import UserProfileSerializer

from mqtt.tests.client import MQTTTestCase

logger = logging.getLogger(__name__)

# TODO: Test admin permissions for staff that is not superuser


class MyTestCase(MQTTTestCase):

    @classmethod
    def setUpClass(cls):
        # create server
        super().setUpClass()

        # instantiate client
        cls.client = Client()


class TestProfile(MyTestCase):

    def test_user_profile_serializer(self):
        self.maxDiff = None

        # test ProfileSerializer

        # super will see all ambulances and hospitals
        u = self.u1
        serializer = UserProfileSerializer(u)
        result = {
            'ambulances': [
                {
                    'ambulance_id': e.pk,
                    'ambulance_identifier': e.identifier,
                    'can_read': True,
                    'can_write': True
                }
                for e in Ambulance.objects.all()
            ],
            'hospitals': [
                {
                    'hospital_id': e.pk,
                    'hospital_name': e.name,
                    'can_read': True,
                    'can_write': True
                }
                for e in Hospital.objects.all()
            ]
        }
        self.assertDictEqual(serializer.data, result)

        # regular users is just like ProfileSerializer
        for u in (self.u2, self.u3):
            serializer = UserProfileSerializer(u)
            result = {
                'ambulances': [
                    {
                        'ambulance_id': e.ambulance.pk,
                        'ambulance_identifier': e.ambulance.identifier,
                        'can_read': e.can_read,
                        'can_write': e.can_write
                    }
                    for e in u.userambulancepermission_set.all()
                ],
                'hospitals': [
                    {
                        'hospital_id': e.hospital.pk,
                        'hospital_name': e.hospital.name,
                        'can_read': e.can_read,
                        'can_write': e.can_write
                    }
                    for e in u.userhospitalpermission_set.all()
                ]
            }
            self.assertDictEqual(serializer.data, result)

        # regular users is just like ProfileSerializer with groups
        u = self.u4
        g = self.g2
        serializer = UserProfileSerializer(u)
        result = {
            'ambulances': [
                {
                    'ambulance_id': e.ambulance.pk,
                    'ambulance_identifier': e.ambulance.identifier,
                    'can_read': e.can_read,
                    'can_write': e.can_write
                }
                for e in g.groupambulancepermission_set.all()
            ],
            'hospitals': [
                {
                    'hospital_id': e.hospital.pk,
                    'hospital_name': e.hospital.name,
                    'can_read': e.can_read,
                    'can_write': e.can_write
                }
                for e in g.grouphospitalpermission_set.all()
            ]
        }
        self.assertDictEqual(serializer.data, result)

        # regular users is just like ProfileSerializer with groups
        u = self.u5
        g = self.g2


class TestProfileViewset(MyTestCase):

    def test_profile_viewset(self):
        # instantiate client
        client = Client()

        # login as admin
        client.login(username=settings.MQTT['USERNAME'], password=settings.MQTT['PASSWORD'])

        # retrieve own
        response = client.get('/en/api/user/{}/profile/'.format(str(self.u1.username)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = UserProfileSerializer(self.u1).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/en/api/user/{}/profile/'.format(str(self.u2.username)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = UserProfileSerializer(self.u2).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/en/api/user/{}/profile/'.format(str(self.u3.username)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = UserProfileSerializer(self.u3).data
        self.assertDictEqual(result, answer)

        # logout
        client.logout()

        # login as testuser1
        client.login(username='testuser1', password='top_secret')

        # retrieve own
        response = client.get('/en/api/user/{}/profile/'.format(str(self.u2.username)),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        result = JSONParser().parse(BytesIO(response.content))
        answer = UserProfileSerializer(self.u2).data
        self.assertDictEqual(result, answer)

        # retrieve someone else's
        response = client.get('/en/api/user/{}/profile/'.format(str(self.u1.username)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        response = client.get('/en/api/user/{}/profile/'.format(str(self.u3.username)),
                              follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        client.logout()


class TestLogin(MyTestCase):

    def test_login(self):
        # blank login
        response = self.client.get('/en/auth/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = self.client.post('/en/auth/login/', {'username': 'testuser11',
                                                     'password': 'top_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)

        # incorrect password
        response = self.client.post('/en/auth/login/', {'username': 'testuser1',
                                                     'password': 'top_secret0'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)

        # correct login
        response = self.client.post('/en/auth/login/', {'username': 'testuser1',
                                                     'password': 'top_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser1')
        self.assertEqual(response.context['user'].is_superuser, False)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)

        # login user2
        response = self.client.post('/en/auth/login/', {'username': 'testuser2',
                                                     'password': 'very_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser2')
        self.assertEqual(response.context['user'].is_superuser, False)

        # login admin
        response = self.client.post('/en/auth/login/', {'username': settings.MQTT['USERNAME'],
                                                     'password': settings.MQTT['PASSWORD']},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, settings.MQTT['USERNAME'])
        self.assertEqual(response.context['user'].is_superuser, True)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)


class TestMQTTLogin(MyTestCase):

    def test_mqtt_login(self):
        # blank login
        response = self.client.get('/en/auth/mqtt/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'testuser11',
                                     'password': 'top_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': 'testuser11'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'testuser1',
                                     'password': 'top_secret0'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': 'testuser1'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # correct login
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'testuser1',
                                     'password': 'top_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': 'testuser1'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

        # login user2
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'testuser2',
                                     'password': 'very_secret'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': 'testuser2'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': settings.MQTT['USERNAME']},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # login admin
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': settings.MQTT['USERNAME'],
                                     'password': settings.MQTT['PASSWORD']},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # username superuser
        response = self.client.post('/en/auth/mqtt/superuser/',
                                    {'username': settings.MQTT['USERNAME']},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)


class TestMQTTACLSubscribe(MyTestCase):

    def test_mqtt_acl_subscribe(self):
        # Settings

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/settings'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # Profile

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/user/testuser1/profile'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '2',
                                     'topic': '/user/testuser1/profile'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # Hospitals

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h1.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h3.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h2.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/hospital/{}/data'.format(self.h1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/hospital/{}/data'.format(self.h3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/hospital/{}/data'.format(self.h2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/item/1/data'.format(self.h1.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/item/2/data'.format(self.h3.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/item/3/data'.format(self.h2.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h1.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h3.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/equipment/{}/metadata'.format(self.h2.equipmentholder.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # Ambulances

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': 'test_client',
                                     'acc': '1',
                                     'topic': '/ambulance/{}/data'.format(self.a2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)


class TestMQTTACLPublish(MyTestCase):

    def test_mqtt_acl_publish(self):
        # Ambulance data

        # can't publish
        clientid = 'test_client'
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/ambulance/{}/data'.format(clientid, self.a1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/ambulance/{}/data'.format(clientid, self.a2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/ambulance/{}/data'.format(clientid, self.a3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/ambulance/{}/data'.format(clientid, self.a1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/ambulance/{}/data'.format(clientid, self.a2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/ambulance/{}/data'.format(clientid, self.a3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # Hospital data

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/hospital/{}/data'.format(clientid, self.h1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/hospital/{}/data'.format(clientid, self.h2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser1',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser1/client/{}/hospital/{}/data'.format(clientid, self.h3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/hospital/{}/data'.format(clientid, self.h1.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/hospital/{}/data'.format(clientid, self.h2.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': 'testuser2',
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/testuser2/client/{}/hospital/{}/data'.format(clientid, self.h3.id)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # Client data

        username = 'testuser2'
        clientid = 'test_client'
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': username,
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/{}/client/{}/status'.format(username, clientid)},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # invalid username

        username = 'testuser2'
        clientid = 'test_client'
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': username,
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/{}/client/{}/status'.format(username + 'o', clientid)},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # invalid clientid

        username = 'testuser2'
        clientid = 'test_client'
        response = self.client.post('/en/auth/mqtt/acl/',
                                    {'username': username,
                                     'clientid': clientid,
                                     'acc': '2',
                                     'topic': '/user/{}/client/{}/status'.format(username, clientid + 'o')},
                                    follow=True)
        self.assertEqual(response.status_code, 403)


class TestMQTTLoginTempPassword(MyTestCase):

    def test(self):
        # instantiate client
        client = Client()

        # retrieve password hash without being logged in
        username = 'admin'
        response = client.get('/en/api/user/{}/password/'.format(username),
                              follow=True)
        result = JSONParser().parse(BytesIO(response.content))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(result,
                         {'detail': 'Authentication credentials were not provided.'})

        # login as admin
        username = settings.MQTT['USERNAME']
        client.login(username=settings.MQTT['USERNAME'],
                     password=settings.MQTT['PASSWORD'])

        # retrieve password hash
        response = client.get('/en/api/user/{}/password/'.format(username),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        encoded = JSONParser().parse(BytesIO(response.content))

        # retrieve temporary password
        password = TemporaryPassword.objects.get(user__username=username).password

        self.assertEqual(check_password(password, encoded), True)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # mqtt login with correct temporary password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'admin',
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # mqtt login with incorrect username
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'admino',
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # mqtt login with incorrect encoded password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': 'admin',
                                     'password': encoded + 'r'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # login as testuser1
        username = 'testuser1'
        client.login(username=username, password='top_secret')

        # retrieve password hash
        response = client.get('/en/api/user/{}/password/'.format(username),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        encoded = JSONParser().parse(BytesIO(response.content))

        # retrieve temporary password
        password = TemporaryPassword.objects.get(user__username=username).password

        self.assertEqual(check_password(password, encoded), True)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # mqtt login with correct temporary password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username,
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # mqtt login with incorrect username
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username + 'o',
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # mqtt login with incorrect encoded password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username,
                                     'password': encoded + 'r'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # login as testuser2
        username = 'testuser2'
        client.login(username=username, password='very_secret')

        # retrieve password hash
        response = client.get('/en/api/user/{}/password/'.format(username),
                              follow=True)
        self.assertEqual(response.status_code, 200)
        encoded = JSONParser().parse(BytesIO(response.content))

        # retrieve temporary password
        password = TemporaryPassword.objects.get(user__username=username).password

        self.assertEqual(check_password(password, encoded), True)

        # logout
        response = self.client.get('/en/auth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # mqtt login with correct temporary password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username,
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        # mqtt login with incorrect username
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username + 'o',
                                     'password': encoded},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        # mqtt login with incorrect encoded password
        response = self.client.post('/en/auth/mqtt/login/',
                                    {'username': username,
                                     'password': encoded + 'r'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)
