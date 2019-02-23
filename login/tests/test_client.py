import logging

from ambulance.models import Ambulance
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestClient(TestSetup):

    def testAmbulanceLogin(self):

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        # login ambulance a1
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a1.identifier)

        # logout ambulance
        client1.ambulance = None
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a1.identifier)

        # login ambulance a2
        client1.ambulance = self.a2
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a2)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a2.identifier)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')
