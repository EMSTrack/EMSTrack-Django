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
            username='testuser1',
            email='test@user.com',
            password='top_secret')

    def test_login(self):

        # instantiate client
        client = Client()

        # blank login
        response = client.get('/aauth/login/')
        self.assertEqual(response.status_code, 200)

        # correct login
        response = client.post('/aauth/login/', { 'username': 'testuser1',
                                                  'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)

        # incorrect username
        response = client.post('/aauth/login/', { 'username': 'testuser11',
                                                 'password': 'top_secret' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'errors', 'This field is required.')

        # incorrect password
        response = client.post('/aauth/login/', { 'username': 'testuser1',
                                                 'password': 'top_secret0' },
                               follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'errors', 'This field is required.')
        
