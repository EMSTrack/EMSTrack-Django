import logging

from django.utils import timezone

from ambulance.models import Ambulance
from emstrack.tests.util import date2iso
from hospital.models import Hospital
from login.models import Client, ClientStatus, ClientLog, ClientActivity
from login.serializers import ClientSerializer
from login.tests.setup_data import TestSetup

logger = logging.getLogger(__name__)


class TestClient(TestSetup):

    def testAmbulance(self):

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

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 1)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 2)

        # go online with ambulance
        client1.status = ClientStatus.O.name
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 4)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a1.identifier)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 6)

        # client online
        client1.status = ClientStatus.O.name
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 7)

        # login ambulance a1
        client1.ambulance = self.a1
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a1)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 9)

        # logout ambulance
        client1.ambulance = None
        client1.save()

        a = Ambulance.objects.get(id=self.a1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a1.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 11)

        # login ambulance a2
        client1.ambulance = self.a2
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, self.a2)
        self.assertEqual(a.client, client1)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.AI.name)
        self.assertEqual(log.details, self.a2.identifier)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 13)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        a = Ambulance.objects.get(id=self.a2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(a, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.AO.name)
        self.assertEqual(log.details, self.a2.identifier)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 15)

    def testHospital(self):

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

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 1)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 2)

        # go online with hospital
        client1.status = ClientStatus.O.name
        client1.hospital = self.h1
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h1)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 4)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h1.name)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 6)

        # client online
        client1.status = ClientStatus.O.name
        client1.save()

        h = Ambulance.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 7)

        # login hospital a1
        client1.hospital = self.h1
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h1)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 9)

        # logout ambulance
        client1.hospital = None
        client1.save()

        h = Hospital.objects.get(id=self.h1.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h1.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 11)

        # login ambulance a2
        client1.hospital = self.h2
        client1.save()

        h = Hospital.objects.get(id=self.h2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.O.name)
        self.assertEqual(client1.hospital, self.h2)
        self.assertEqual(h.client, client1)
        self.assertEqual(client1.ambulance, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HI.name)
        self.assertEqual(log.details, self.h2.name)

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.O.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 13)

        # go offline
        client1.status = ClientStatus.F.name
        client1.save()

        h = Hospital.objects.get(id=self.h2.id)
        client1 = Client.objects.get(id=client1.id)

        self.assertEqual(client1.status, ClientStatus.F.name)
        self.assertEqual(client1.ambulance, None)
        self.assertFalse(hasattr(h, 'client'))
        self.assertEqual(client1.hospital, None)

        log = ClientLog.objects.filter(client=client1).latest('updated_on')
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HS.name)
        self.assertEqual(log.details, '')

        log = ClientLog.objects.filter(client=client1).order_by('-updated_on')[1]
        self.assertEqual(log.client, client1)
        self.assertEqual(log.status, ClientStatus.F.name)
        self.assertEqual(log.activity, ClientActivity.HO.name)
        self.assertEqual(log.details, self.h2.name)

        self.assertEqual(len(ClientLog.objects.filter(client=client1)), 15)

    def testClientSerializer(self):

        # test ClientSerializer

        # client online
        client1 = Client.objects.create(client_id='client_id_1', user=self.u1,
                                        status=ClientStatus.O.name, ambulance=self.a1)

        serializer = ClientSerializer(client1)
        result = {
            'id': client1.id,
            'client_id': client1.client_id,
            'user': client1.user.id,
            'status': client1.status,
            'ambulance': client1.ambulance.id,
            'hospital': None,
            'updated_on': date2iso(client1.updated_on)
        }
        self.assertDictEqual(serializer.data, result)

        timestamp = timezone.now()
        serializer = ClientSerializer(data={
            'client_id': 'client_id_3',
            'status': ClientStatus.O.name,
            'ambulance': None,
            'hospital': None,
            'updated_on': date2iso(timestamp)
        })
        serializer.is_valid()
        serializer.save(user=self.u2)

        client2 = Client.objects.get(client_id='client_id_3')

        self.assertEqual(client2.status, ClientStatus.O.name)
        self.assertEqual(client2.ambulance, None)
        self.assertEqual(client2.hospital, None)
        self.assertEqual(client2.updated_on, timestamp)

