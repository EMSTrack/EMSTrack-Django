from django.test import TestCase

from django.contrib.auth.models import User
from django.conf import settings

from ambulances.models import Hospital, HospitalPermission

from django.test import Client

from ..views import LoginView, SignupView, LogoutView, MQTTLoginView, MQTTSuperuserView, MQTTAclView

from ambulances.tests.mqtt import MQTTTestCase, MQTTTestClient

class MyTestCase(MQTTTestCase):

    @classmethod
    def setUpClass(cls):

        # create server
        super().setUpClass()

        # set up data
        cls.setUpTestData()
        
        # instantiate client
        cls.client = Client()

    @classmethod
    def setUpTestData(cls):

        # Retrieve admin
        cls.u1 = User.objects.get(username=settings.MQTT['USERNAME'])

        try:
            
            # Add users
            cls.u2 = User.objects.get(username='testuser1')
            cls.u3 = User.objects.get(username='testuser2')

            # Add hospitals
            cls.h1 = Hospital.objects.get(name='hospital1')
            cls.h2 = Hospital.objects.get(name='hospital2')
            cls.h3 = Hospital.objects.get(name='hospital3')

        except:

            # Add users
            cls.u2 = User.objects.create_user(
                username='testuser1',
                email='test1@user.com',
                password='top_secret')
        
            cls.u3 = User.objects.create_user(
                username='testuser2',
                email='test2@user.com',
                password='very_secret')
        
            # Add hospitals
            cls.h1 = Hospital.objects.create(name='hospital1',
                                             address='somewhere',
                                             updated_by=cls.u1)
            cls.h2 = Hospital.objects.create(name='hospital2',
                                             address='somewhere else',
                                             updated_by=cls.u1)
            cls.h3 = Hospital.objects.create(name='hospital3',
                                             address='somewhere other',
                                             updated_by=cls.u1)
            
            # Add permissions
            cls.u2.profile.hospitals.add(
                HospitalPermission.objects.create(hospital=cls.h1,
                                                  can_write=True),
                HospitalPermission.objects.create(hospital=cls.h3)
            )
            
            cls.u3.profile.hospitals.add(
                HospitalPermission.objects.create(hospital=cls.h1),
                HospitalPermission.objects.create(hospital=cls.h2,
                                                  can_write=True)
            )

class TestLogin(MyTestCase):
            
    def test_login(self):

        # blank login
        response = self.client.get('/aauth/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = self.client.post('/aauth/login/', { 'username': 'testuser11',
                                                  'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
        # incorrect password
        response = self.client.post('/aauth/login/', { 'username': 'testuser1',
                                                  'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
        # correct login
        response = self.client.post('/aauth/login/', { 'username': 'testuser1',
                                                  'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser1')
        self.assertEqual(response.context['user'].is_superuser, False)

        # logout
        response = self.client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)

        # login user2
        response = self.client.post('/aauth/login/', { 'username': 'testuser2',
                                                  'password': 'very_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser2')
        self.assertEqual(response.context['user'].is_superuser, False)

        # login admin
        response = self.client.post('/aauth/login/', { 'username': settings.MQTT['USERNAME'],
                                                  'password': settings.MQTT['PASSWORD'] },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, settings.MQTT['USERNAME'])
        self.assertEqual(response.context['user'].is_superuser, True)

        # logout
        response = self.client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
class TestMQTTLogin(MyTestCase):

    def test_mqtt_login(self):

        # blank login
        response = self.client.get('/aauth/mqtt/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser11',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser11' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect password
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # correct login
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # logout
        response = self.client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

        # login user2
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser2',
                                 'password': 'very_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser2' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': settings.MQTT['USERNAME'] },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # login admin
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'password': settings.MQTT['PASSWORD'] },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # username superuser
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': settings.MQTT['USERNAME'] },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # logout
        response = self.client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

class TestMQTTACLPublish(MyTestCase):

    def test_mqtt_acl_publish(self):
        
        # login
        response = self.client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # not super
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/hospital' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/ambulance' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/location' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/llocation' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong user in topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser2/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # super behaves the same because it never gets acl tested
        response = self.client.post('/aauth/mqtt/superuser/',
                               { 'username': settings.MQTT['USERNAME'] },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/hospital' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/ambulance' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/location' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/admin/llocation' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong user in topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser2/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can't publish wrong topic
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': settings.MQTT['USERNAME'],
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

class TestMQTTACLSubscribe(MyTestCase):

    def test_mqtt_acl_subscribe(self):
        
        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/user/testuser1/hospitals' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't publish
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/hospitals' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h1.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h3.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/metadata'.format(self.h2.id) },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/rx'.format(self.h1.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/beds'.format(self.h3.id) },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can't subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/hospital/{}/equipment/rx'.format(self.h2.id) },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can subscribe
        response = self.client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '1',
                                 'topic': '/user/testuser1/ambulances' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
