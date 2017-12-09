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
            password='admin')

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

        # login admin
        response = client.post('/aauth/login/', { 'username': 'admin',
                                                  'password': 'admin' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, True)
        self.assertEqual(response.context['user'].username, 'admin')

        # logout
        response = client.get('/aauth/logout/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].is_authenticated, False)
        
