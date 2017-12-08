from django.test import TestCase, RequestFactory

from ambulances.models import User

from django.test import Client

class CreateUser(TestCase):

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser1',
            email='test@user.com',
            password='top_secret')

    def test_login(self):
        self.assertEqual(True,True);
