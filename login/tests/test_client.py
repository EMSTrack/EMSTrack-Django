import logging

from login.models import Client, ClientStatus, ClientLog
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestClient(TestSetup):

    def testSave(self):

        # client online
        client1 = Client.objects.create(client='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        # login ambulance
        client1.ambulance = self.a
        client1.save()

        self.assertEqual(client1.ambulance, self.a)
        self.assertEqual(client1.hospital, None)

