import logging

from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from login.tests.setup_data import TestSetup

from login.serializers import TokenLoginSerializer

logger = logging.getLogger(__name__)


class TestTokenLogin(TestSetup):

    def test_serializer(self):
        self.maxDiff = None

        # test ProfileSerializer

        # super will see all ambulances and hospitals
        u = self.u1
        serializer = TokenLoginSerializer(username=u.username)
        self.assertEqual(serializer.data['url'], None)
        self.assertTrue(len(serializer.data['token']) == 50)
