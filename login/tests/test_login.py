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

        # Create an instance of a GET request.
        request = self.factory.get('/aauth/login')

        #request.user = self.user
        #request.user = AnonymousUser()

        response = LoginView.as_view()(request)
        
        self.assertEqual(response.status_code, 200)
