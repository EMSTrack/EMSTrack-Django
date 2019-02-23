import logging

from ambulance.models import Ambulance
from login.models import Client, ClientStatus, ClientLog
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestClient(TestSetup):

    def testSave(self):

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        # login ambulance
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1)

        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        # logout ambulance
        client1.ambulance = None
        client1.save()

        a = Ambulance.objects.get(id=self.a1)

        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

