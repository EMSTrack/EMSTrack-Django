from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model
User = get_user_model()

from django.test import Client

from ..views import LoginView, SignupView, LogoutView, MQTTLoginView, MQTTSuperuserView, MQTTAclView

class CreateUser(TestCase):

    def setUp(self):

        # Every test needs access to the request factory.
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username='admin',
            email='admin@user.com',
            password='admin',
            is_superuser=True)

        self.user = User.objects.create_user(
            username='testuser1',
            email='test1@user.com',
            password='top_secret')

        self.user = User.objects.create_user(
            username='testuser2',
            email='test2@user.com',
            password='very_secret')
        
    def test_login(self):

        # instantiate client
        client = Client()

        # blank login
        response = client.get('/aauth/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = client.post('/aauth/login/', { 'username': 'testuser11',
                                                  'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
        # incorrect password
        response = client.post('/aauth/login/', { 'username': 'testuser1',
                                                  'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
        # correct login
        response = client.post('/aauth/login/', { 'username': 'testuser1',
                                                  'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser1')
        self.assertEqual(response.context['user'].is_superuser, False)

        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)

        # login user2
        response = client.post('/aauth/login/', { 'username': 'testuser2',
                                                  'password': 'very_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'testuser2')
        self.assertEqual(response.context['user'].is_superuser, False)

        # login admin
        response = client.post('/aauth/login/', { 'username': 'admin',
                                                  'password': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'admin')
        self.assertEqual(response.context['user'].is_superuser, True)

        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
    def test_mqtt_login(self):

        # instantiate client
        client = Client()
        
        # blank login
        response = client.get('/aauth/mqtt/login/')
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser11',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser11' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # incorrect password
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # correct login
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

        # login user2
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser2',
                                 'password': 'very_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser2' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # login admin
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'admin',
                                 'password': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # username superuser
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_mqtt_acl(self):
        
        # instantiate client
        client = Client()

        # login
        response = client.post('/aauth/mqtt/login/',
                               { 'username': 'testuser1',
                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # not super
        response = client.post('/aauth/mqtt/superuser/',
                               { 'username': 'testuser1' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/hospital' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        
        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/ambulance' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/location' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # can publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser1/llocation' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish wrong user in topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/testuser2/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)

        # can publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user/location' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '/user' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
        
        # can publish wrong topic
        response = client.post('/aauth/mqtt/acl/',
                               { 'username': 'testuser1',
                                 'clientid': 'test_client',
                                 'acc': '2',
                                 'topic': '' },
                               follow=True)
        self.assertEqual(response.status_code, 403)
